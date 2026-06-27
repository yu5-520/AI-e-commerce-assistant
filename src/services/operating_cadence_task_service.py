"""V12.4 operating cadence task service.

V12.4 changes the task source from single baseline alarms to:

    redline hard rules + upload frequency + 3/7/14/30/90 day trend windows
    + agent-style operating judgement + evidence gate.

The service reads product_metric_facts, creates operating cadence signals, saves
candidate tasks for daily/weekly reports, and promotes meaningful signals into
SOP task packages.  It deliberately does not execute business changes.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Tuple
from uuid import uuid4

from src.repositories.sqlite_repository import connect, dumps, ensure_columns, loads
from src.services import module_task_service
from src.services.metric_fact_store_service import ensure_metric_fact_tables
from src.services.task_evidence_gate_service import apply_evidence_gate_to_created_task

OPERATING_CADENCE_VERSION = "12.4.0"
CADENCE_WINDOWS = [3, 7, 14, 30, 90]
TRACKED_METRICS = {
    "inventory_qty",
    "sellable_days",
    "payment_amount",
    "avg_order_value",
    "payment_order_count",
    "payment_unit_count",
    "payment_conversion_rate",
    "roi",
    "ad_spend",
    "click_rate",
    "visitor_count",
    "page_view_count",
    "click_user_count",
    "organic_visitor_count",
    "paid_visitor_count",
    "gross_margin_rate",
    "gross_profit_amount",
    "product_cost_amount",
    "refund_rate",
    "refund_amount",
    "refund_order_count",
}

METRIC_LABELS = {
    "inventory_qty": "库存数量",
    "sellable_days": "可售天数",
    "payment_amount": "支付金额",
    "avg_order_value": "客单价",
    "payment_order_count": "支付订单数",
    "payment_unit_count": "支付件数",
    "payment_conversion_rate": "支付转化率",
    "roi": "ROI",
    "ad_spend": "广告消耗",
    "click_rate": "点击率",
    "visitor_count": "访客数",
    "page_view_count": "浏览量",
    "click_user_count": "点击人数",
    "organic_visitor_count": "自然流量访客数",
    "paid_visitor_count": "付费流量访客数",
    "gross_margin_rate": "毛利率",
    "gross_profit_amount": "毛利金额",
    "product_cost_amount": "商品成本金额",
    "refund_rate": "退款率",
    "refund_amount": "退款金额",
    "refund_order_count": "退款订单数",
}

REDLINE_RULES = {
    "inventory_zero": "库存归零但仍有经营数据，必须人工复核是否断货、下架或补货。",
    "negative_margin": "毛利率触及红线，必须复核售价、成本、优惠和活动承接。",
    "refund_spike": "退款率进入红线区，必须复核售后原因和商品承接。",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}".upper()


def _num(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _pct_change(old: float | None, new: float | None) -> float | None:
    if old is None or new is None:
        return None
    if abs(old) < 1e-9:
        return None
    return (new - old) / abs(old)


def _fmt_change(value: float | None) -> str:
    if value is None:
        return "无法计算"
    return f"{value * 100:+.1f}%"


def _safe_date(value: Any) -> str:
    text = str(value or "").strip()
    return text[:10] if text else "未知日期"


def _date_value(value: Any) -> datetime | None:
    text = _safe_date(value)
    if text == "未知日期":
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _window_bucket(day_span: int) -> Dict[str, Any]:
    if day_span <= 3:
        return {"windowDays": 3, "windowType": "short_wave", "reportTarget": "日报", "label": "3天短波动"}
    if day_span <= 7:
        return {"windowDays": 7, "windowType": "small_trend", "reportTarget": "日报/周报", "label": "7天小趋势"}
    if day_span <= 14:
        return {"windowDays": 14, "windowType": "mid_short_trend", "reportTarget": "周报", "label": "14天中短趋势"}
    if day_span <= 30:
        return {"windowDays": 30, "windowType": "mid_trend", "reportTarget": "周报/月报", "label": "30天中趋势"}
    return {"windowDays": 90, "windowType": "large_trend", "reportTarget": "月报/季报", "label": "90天大趋势"}


def ensure_operating_cadence_tables() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS operating_cadence_signals (
                signal_id TEXT PRIMARY KEY,
                data_version TEXT,
                product_id TEXT,
                store_id TEXT,
                metric_scope TEXT,
                cadence_window TEXT,
                signal_type TEXT,
                risk_level TEXT,
                queue_type TEXT,
                status TEXT,
                task_id TEXT,
                payload TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        ensure_columns(
            conn,
            "operating_cadence_signals",
            {
                "upload_frequency_level": "TEXT",
                "report_target": "TEXT",
                "agent_judgment": "TEXT",
            },
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_operating_cadence_signals_version ON operating_cadence_signals(data_version, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_operating_cadence_signals_product ON operating_cadence_signals(product_id, store_id, created_at)")
        conn.commit()


def _load_facts(limit: int = 5000) -> List[Dict[str, Any]]:
    ensure_metric_fact_tables()
    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT *
            FROM product_metric_facts
            WHERE metric_code IN ({','.join('?' for _ in TRACKED_METRICS)})
              AND (metric_scope IS NULL OR metric_scope = '' OR metric_scope = 'product')
            ORDER BY COALESCE(stat_date, updated_at) ASC, updated_at ASC
            LIMIT ?
            """,
            [*sorted(TRACKED_METRICS), limit],
        ).fetchall()
    return [dict(row) for row in rows]


def _context_for_product(product_id: str | None, store_id: str | None) -> Dict[str, Any]:
    if not product_id:
        return {}
    with connect() as conn:
        if store_id:
            row = conn.execute(
                """
                SELECT * FROM operating_products
                WHERE product_id = ? AND (normalized_store_id = ? OR store_id = ? OR store_name = ?)
                ORDER BY updated_at DESC LIMIT 1
                """,
                (product_id, store_id, store_id, store_id),
            ).fetchone()
        else:
            row = conn.execute("SELECT * FROM operating_products WHERE product_id = ? ORDER BY updated_at DESC LIMIT 1", (product_id,)).fetchone()
    if not row:
        return {"productId": product_id, "storeId": store_id, "title": f"商品 {product_id}", "storeName": store_id or "导入店铺"}
    payload = loads(row["payload"])
    return {
        **payload,
        "productId": row["product_id"],
        "storeId": row["normalized_store_id"] or row["store_id"],
        "storeName": row["normalized_store_name"] or row["store_name"],
        "title": row["title"],
        "platform": row["platform"],
        "category": row["category"],
        "assignedOperatorId": row["assigned_operator_id"],
        "ownerUserId": row["owner_user_id"],
        "reviewerId": row["reviewer_id"],
        "visibleUserIds": payload.get("visibleUserIds") or [],
        "visibleRoleIds": payload.get("visibleRoleIds") or [],
        "dataScopeSource": row["data_scope_source"],
    }


def _upload_cadence(facts: List[Dict[str, Any]]) -> Dict[str, Any]:
    dates = sorted({_safe_date(row.get("stat_date") or row.get("updated_at")) for row in facts if _safe_date(row.get("stat_date") or row.get("updated_at")) != "未知日期"})
    versions = sorted({str(row.get("data_version")) for row in facts if row.get("data_version")})
    if not dates:
        return {"uploadCount": len(versions), "statDateCount": 0, "daySpan": 0, "avgIntervalDays": None, "frequencyLevel": "unknown", "sensitivityMultiplier": 1.0}
    parsed_dates = [item for item in (_date_value(date) for date in dates) if item]
    day_span = (max(parsed_dates) - min(parsed_dates)).days if parsed_dates else 0
    avg_interval = day_span / max(len(dates) - 1, 1) if len(dates) > 1 else None
    if len(dates) >= 3 and day_span <= 7:
        level = "high"
        multiplier = 0.55
    elif avg_interval is not None and avg_interval <= 7:
        level = "medium"
        multiplier = 0.75
    else:
        level = "low"
        multiplier = 1.0
    return {
        "uploadCount": len(versions) or len(dates),
        "statDateCount": len(dates),
        "firstStatDate": dates[0],
        "latestStatDate": dates[-1],
        "daySpan": day_span,
        "avgIntervalDays": avg_interval,
        "frequencyLevel": level,
        "sensitivityMultiplier": multiplier,
        "rule": "上传频率越高，短周期波动阈值越低；红线任务不受阈值降级影响。",
    }


def _entity_metrics(facts: List[Dict[str, Any]]) -> Dict[Tuple[str, str | None], Dict[str, List[Dict[str, Any]]]]:
    grouped: Dict[Tuple[str, str | None], Dict[str, List[Dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in facts:
        product_id = str(row.get("product_id") or row.get("sku_id") or row.get("erp_product_code") or "").strip()
        if not product_id:
            continue
        store_id = str(row.get("store_id") or row.get("store_code") or row.get("store_name") or "").strip() or None
        metric = str(row.get("metric_code") or "").strip()
        if metric not in TRACKED_METRICS:
            continue
        grouped[(product_id, store_id)][metric].append(row)
    for metrics in grouped.values():
        for rows in metrics.values():
            rows.sort(key=lambda item: (_safe_date(item.get("stat_date") or item.get("updated_at")), str(item.get("updated_at") or "")))
    return grouped


def _metric_pair(metrics: Dict[str, List[Dict[str, Any]]], code: str) -> Dict[str, Any]:
    rows = metrics.get(code) or []
    if not rows:
        return {"metricCode": code, "metricName": METRIC_LABELS.get(code, code), "missing": True}
    first = rows[0]
    latest = rows[-1]
    old = _num(first.get("metric_value"))
    new = _num(latest.get("metric_value"))
    return {
        "metricCode": code,
        "metricName": METRIC_LABELS.get(code, code),
        "firstValue": old,
        "latestValue": new,
        "firstDisplayValue": first.get("display_value") or first.get("raw_value"),
        "latestDisplayValue": latest.get("display_value") or latest.get("raw_value"),
        "firstDate": _safe_date(first.get("stat_date") or first.get("updated_at")),
        "latestDate": _safe_date(latest.get("stat_date") or latest.get("updated_at")),
        "changeRate": _pct_change(old, new),
        "factId": latest.get("fact_id"),
        "sourceSheet": latest.get("source_sheet"),
        "sourceBlockId": latest.get("source_block_id"),
        "dataVersion": latest.get("data_version"),
    }


def _signal_base(product: Dict[str, Any], cadence: Dict[str, Any], data_version: str | None, signal_type: str, risk_level: str, queue_type: str, domain: str, reason: str, metrics: List[Dict[str, Any]], score: float) -> Dict[str, Any]:
    window = _window_bucket(int(cadence.get("daySpan") or 0))
    return {
        "version": OPERATING_CADENCE_VERSION,
        "signalId": make_id("CADSIG"),
        "dataVersion": data_version or next((m.get("dataVersion") for m in metrics if m.get("dataVersion")), None),
        "productId": product.get("productId"),
        "storeId": product.get("storeId"),
        "storeName": product.get("storeName"),
        "productTitle": product.get("title") or product.get("productId"),
        "signalType": signal_type,
        "riskLevel": risk_level,
        "queueType": queue_type,
        "riskDomain": domain,
        "metricScope": "product",
        "reason": reason,
        "score": score,
        "metrics": metrics,
        "cadence": cadence,
        "window": window,
        "reportTarget": window.get("reportTarget"),
        "agentJudgment": {
            "status": "v12_4_operating_cadence_agent_judgment",
            "boundary": "红线由硬规则控制；非红线由波动区间和上传频率放大 Agent 判断，但仍经过证据闸门。",
            "reason": reason,
            "cadenceSensitivity": cadence.get("frequencyLevel"),
        },
    }


def _build_signals_for_entity(product: Dict[str, Any], metrics: Dict[str, List[Dict[str, Any]]], cadence: Dict[str, Any], data_version: str | None) -> List[Dict[str, Any]]:
    mult = float(cadence.get("sensitivityMultiplier") or 1.0)
    inventory = _metric_pair(metrics, "inventory_qty")
    payment = _metric_pair(metrics, "payment_amount")
    roi = _metric_pair(metrics, "roi")
    ad_spend = _metric_pair(metrics, "ad_spend")
    conversion = _metric_pair(metrics, "payment_conversion_rate")
    click_rate = _metric_pair(metrics, "click_rate")
    visitors = _metric_pair(metrics, "visitor_count")
    refund_rate = _metric_pair(metrics, "refund_rate")
    gross_margin = _metric_pair(metrics, "gross_margin_rate")

    signals: List[Dict[str, Any]] = []
    product_name = product.get("title") or product.get("productId")

    inv_latest = inventory.get("latestValue")
    pay_latest = payment.get("latestValue")
    if inv_latest is not None and inv_latest <= 0 and (pay_latest is None or pay_latest >= 0):
        signals.append(_signal_base(product, cadence, data_version, "redline_inventory_zero", "高", "urgent_execution", "库存", f"{product_name} 库存已归零，需要立即复核断货、补货或下架承接。", [inventory, payment, conversion], 100))

    gm_latest = gross_margin.get("latestValue")
    if gm_latest is not None and gm_latest < 0.2:
        signals.append(_signal_base(product, cadence, data_version, "redline_margin_floor", "高", "urgent_execution", "利润", f"{product_name} 毛利率低于 20% 红线，需要复核售价、成本、优惠和活动策略。", [gross_margin, payment, roi], 95))

    rr_latest = refund_rate.get("latestValue")
    rr_change = refund_rate.get("changeRate")
    if rr_latest is not None and (rr_latest >= 0.08 or (rr_change is not None and rr_change >= 0.5)):
        signals.append(_signal_base(product, cadence, data_version, "redline_refund_watch", "高" if rr_latest >= 0.12 else "中", "urgent_execution" if rr_latest >= 0.12 else "today_execution", "售后", f"{product_name} 退款率进入关注区，需要复核退款理由和售后承接。", [refund_rate, payment], 90 if rr_latest >= 0.12 else 70))

    inv_change = inventory.get("changeRate")
    pay_change = payment.get("changeRate")
    if inv_change is not None and inv_change <= -(0.20 * mult) and (pay_change is None or pay_change >= -0.05):
        signals.append(_signal_base(product, cadence, data_version, "inventory_consumption_opportunity", "中", "daily_operating_task", "库存", f"{product_name} 库存 {_fmt_change(inv_change)}，支付金额 {_fmt_change(pay_change)}，存在补货、主推承接或断货风险复核需求。", [inventory, payment, conversion], 82))

    ad_change = ad_spend.get("changeRate")
    roi_change = roi.get("changeRate")
    if ad_change is not None and ad_change >= (0.25 * mult) and roi_change is not None and roi_change <= -(0.08 * mult):
        signals.append(_signal_base(product, cadence, data_version, "ad_efficiency_review", "中", "daily_operating_task", "投产", f"{product_name} 广告消耗 {_fmt_change(ad_change)}，ROI {_fmt_change(roi_change)}，需要复核投放质量、关键词、人群和预算节奏。", [ad_spend, roi, payment, click_rate, conversion], 80))

    conv_change = conversion.get("changeRate")
    if conv_change is not None and conv_change <= -(0.12 * mult) and (pay_change is None or pay_change <= 0.10):
        signals.append(_signal_base(product, cadence, data_version, "conversion_drop_review", "中", "daily_operating_task", "流量", f"{product_name} 支付转化率 {_fmt_change(conv_change)}，需要复核主图、详情页、价格和客服承接。", [conversion, click_rate, visitors, payment], 76))

    if pay_change is not None and pay_change <= -(0.18 * mult):
        signals.append(_signal_base(product, cadence, data_version, "payment_decline_review", "中", "daily_operating_task", "趋势", f"{product_name} 支付金额 {_fmt_change(pay_change)}，需要排查流量、转化、库存和活动承接变化。", [payment, visitors, conversion, inventory], 74))

    if pay_change is not None and pay_change >= (0.18 * mult) and (roi_change is None or roi_change >= -(0.05 * mult)):
        signals.append(_signal_base(product, cadence, data_version, "growth_opportunity_capture", "中", "daily_operating_task", "趋势", f"{product_name} 支付金额 {_fmt_change(pay_change)}，ROI 未明显恶化，建议复核是否加库存、加主推位或放大优质流量。", [payment, roi, inventory, visitors], 78))

    return signals


def _actions_for_signal(signal: Dict[str, Any]) -> List[str]:
    domain = signal.get("riskDomain")
    if signal.get("signalType") == "redline_inventory_zero":
        return ["6小时内核对真实库存、可售天数和在途库存。", "6小时内确认是否暂停投放、下架缺货链接或切换替代主推品。", "12小时内给出补货、替换主推位或客服承接话术结论。"]
    if domain == "库存":
        return ["24小时内复核近7日销量、库存和可售天数。", "判断是否需要补货、调拨、降低投放或替换主推位。", "提交库存截图、销售趋势截图和处理结论。"]
    if domain == "投产":
        return ["12小时内复核广告消耗、ROI、点击率和转化率。", "拆分关键词、人群、渠道或素材，找出消耗上升但效率下降的来源。", "提交预算调整建议；未复核前不自动加大投放。"]
    if domain == "流量":
        return ["24小时内复核主图、标题、详情页、价格和客服承接。", "对比自然流量与付费流量变化，判断是否流量质量变化。", "提交一项可执行测试方案，如换主图、换标题或详情页检查。"]
    if domain == "售后":
        return ["12小时内整理退款理由 TOP5。", "复核商品质量、尺码、发货、客服承接和页面描述是否存在异常。", "提交售后原因截图和处理方案。"]
    return ["24小时内复核该商品 3/7/14 天趋势变化。", "判断是否进入补货、投放、主推位或价格策略调整。", "提交数据截图和下一步动作建议。"]


def _task_payload(signal: Dict[str, Any]) -> Dict[str, Any]:
    product = _context_for_product(signal.get("productId"), signal.get("storeId"))
    actions = _actions_for_signal(signal)
    risk_level = signal.get("riskLevel") or "中"
    queue_type = signal.get("queueType") or "daily_operating_task"
    deadline = "6小时内" if risk_level == "高" else "今日内" if queue_type == "daily_operating_task" else "本周内"
    title = signal.get("productTitle") or product.get("title") or signal.get("productId") or "经营对象"
    subtitle = "红线强制复核" if risk_level == "高" else "今日经营调整" if queue_type == "daily_operating_task" else "周期复盘"
    evidence_pack = [
        {
            "type": "operating_cadence_signal",
            "title": item.get("metricName") or item.get("metricCode"),
            "metric": item.get("latestDisplayValue") or item.get("latestValue"),
            "reason": f"{item.get('metricName')} {item.get('firstDisplayValue')} → {item.get('latestDisplayValue')}，变化 {_fmt_change(item.get('changeRate'))}",
            "dataVersion": item.get("dataVersion") or signal.get("dataVersion"),
            "sourceSheet": item.get("sourceSheet"),
            "sourceBlockId": item.get("sourceBlockId"),
        }
        for item in signal.get("metrics") or []
        if not item.get("missing")
    ]
    ownership = {
        "assignedOperatorId": product.get("assignedOperatorId"),
        "ownerUserId": product.get("ownerUserId") or product.get("assignedOperatorId"),
        "reviewerId": product.get("reviewerId"),
        "visibleUserIds": list(dict.fromkeys([item for item in [product.get("assignedOperatorId"), product.get("ownerUserId"), product.get("reviewerId"), *(product.get("visibleUserIds") or [])] if item])),
        "visibleRoleIds": list(dict.fromkeys([*(product.get("visibleRoleIds") or []), "owner", "manager", "operator"])),
        "dataScopeSource": product.get("dataScopeSource") or "uploader_account",
        "rule": "V12.4 任务继承商品/店铺归属，日报/周报候选不反向制造权限。",
    }
    detail = {
        "version": OPERATING_CADENCE_VERSION,
        "title": f"经营节奏任务｜{title} · {subtitle}",
        "warningSummary": signal.get("reason"),
        "cadence": signal.get("cadence"),
        "window": signal.get("window"),
        "evidencePack": evidence_pack,
        "sopSteps": actions,
        "reviewMetrics": {"metricScope": "product", "requiredFactTables": ["product_metric_facts"], "cadenceWindow": (signal.get("window") or {}).get("label")},
        "completionGate": ["提交指标截图或报表数据", "说明是否执行调整", "总管复核后进入日报/周报复盘"],
        "failureThreshold": {"riskLevel": risk_level, "queueType": queue_type, "rule": "红线必须处理；波动任务未复核前不得自动放大投放或库存动作。"},
        "agentBoundary": "Agent 负责经营判断和 SOP，不直接改预算、库存、价格或店铺数据。",
    }
    return {
        "id": make_id("CADTASK"),
        "taskGenerationMode": "v11_8_sop_package",
        "title": title,
        "taskCard": {"title": title, "subtitle": subtitle, "deadline": deadline, "priority": risk_level, "ownerRole": "运营" if ownership.get("assignedOperatorId") else "总管"},
        "taskDetailReport": detail,
        "evidencePack": evidence_pack,
        "sopSteps": actions,
        "reviewMetrics": detail["reviewMetrics"],
        "completionGate": detail["completionGate"],
        "failureThreshold": detail["failureThreshold"],
        "task": actions[0],
        "taskType": "红线强制复核任务" if risk_level == "高" else "今日经营调整任务" if queue_type == "daily_operating_task" else "周期经营复盘任务",
        "priority": risk_level,
        "deadline": deadline,
        "timeBucket": deadline,
        "urgencyLevel": "urgent" if risk_level == "高" else "today" if queue_type == "daily_operating_task" else "weekly",
        "queueType": queue_type,
        "displayState": "expanded",
        "source": "经营节奏Agent",
        "sourceModule": "经营节奏Agent",
        "sourceRoute": "business-actions",
        "productId": signal.get("productId"),
        "entityId": signal.get("productId"),
        "entityType": "商品",
        "store": product.get("storeName") or signal.get("storeName") or signal.get("storeId") or "导入店铺",
        "storeName": product.get("storeName") or signal.get("storeName"),
        "storeIds": [signal.get("storeId")] if signal.get("storeId") else [],
        "visibleStoreIds": [signal.get("storeId")] if signal.get("storeId") else [],
        "platform": product.get("platform") or "未知平台",
        "category": product.get("category") or "未分类",
        "riskDomain": signal.get("riskDomain"),
        "metricScope": "product",
        "actionType": "红线复核" if risk_level == "高" else "经营调整" if queue_type == "daily_operating_task" else "周期复盘",
        "taskLayer": "manager_dispatch" if risk_level == "高" else "operator_execution",
        "assigneeId": ownership.get("assignedOperatorId") if risk_level != "高" else None,
        "reviewerId": ownership.get("reviewerId"),
        "visibleUserIds": ownership.get("visibleUserIds"),
        "visibleRoleIds": ["owner", "manager", "finance"] if risk_level == "高" else ownership.get("visibleRoleIds"),
        "ownership": ownership,
        "sourceEvent": f"V124:{signal.get('dataVersion') or 'latest'}:{signal.get('productId')}:{signal.get('signalType')}:{(signal.get('window') or {}).get('windowType')}",
        "riskGrade": risk_level,
        "riskPolicy": {"riskMode": "operating_cadence", "requiresEvidenceGate": True, "requiresApproval": risk_level == "高", "rule": "V12.4 红线硬控；波动区间由Agent判断后生成经营任务或候选任务。"},
        "investmentApplicationAllowed": False,
        "executionAllowed": risk_level != "高",
        "approvalChain": ["总管复核"] if risk_level == "高" else [],
        "executionRequirements": actions,
        "judgmentTags": ["V12.4经营节奏", risk_level, signal.get("riskDomain"), queue_type, (signal.get("window") or {}).get("label"), signal.get("cadence", {}).get("frequencyLevel")],
        "evidence": evidence_pack,
        "reason": signal.get("reason"),
        "agentJudgment": signal.get("agentJudgment"),
        "sourceTrail": ["报表中心", "指标事实表", "经营节奏Agent", "任务证据闸门", "日报/周报候选"],
        "recapTarget": "日报" if queue_type == "daily_operating_task" or risk_level == "高" else "周报",
    }


def _save_signal(signal: Dict[str, Any], status: str, task_id: str | None = None) -> Dict[str, Any]:
    ensure_operating_cadence_tables()
    payload = {**signal, "status": status, "taskId": task_id}
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO operating_cadence_signals (
                signal_id, data_version, product_id, store_id, metric_scope, cadence_window,
                signal_type, risk_level, queue_type, status, task_id, payload, created_at,
                upload_frequency_level, report_target, agent_judgment
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                signal.get("signalId"),
                signal.get("dataVersion"),
                signal.get("productId"),
                signal.get("storeId"),
                signal.get("metricScope") or "product",
                (signal.get("window") or {}).get("windowType"),
                signal.get("signalType"),
                signal.get("riskLevel"),
                signal.get("queueType"),
                status,
                task_id,
                dumps(payload),
                now_iso(),
                (signal.get("cadence") or {}).get("frequencyLevel"),
                signal.get("reportTarget"),
                dumps(signal.get("agentJudgment") or {}),
            ),
        )
        conn.commit()
    return payload


def generate_operating_cadence_tasks(data_version: str | None = None, *, max_tasks: int = 16) -> Dict[str, Any]:
    ensure_operating_cadence_tables()
    facts = _load_facts()
    if data_version:
        # Keep cadence frequency global, but promote latest-version signals first.
        target_facts = [row for row in facts if str(row.get("data_version") or "") == str(data_version)]
        if not target_facts:
            target_facts = facts
    else:
        target_facts = facts
    cadence = _upload_cadence(facts)
    grouped = _entity_metrics(facts)
    latest_version = data_version or next((row.get("data_version") for row in reversed(facts) if row.get("data_version")), None)
    signals: List[Dict[str, Any]] = []
    for (product_id, store_id), metrics in grouped.items():
        product = _context_for_product(product_id, store_id)
        signals.extend(_build_signals_for_entity(product, metrics, cadence, latest_version))
    signals.sort(key=lambda item: (0 if item.get("riskLevel") == "高" else 1, -float(item.get("score") or 0), item.get("productId") or ""))

    tasks: List[Dict[str, Any]] = []
    candidate_count = 0
    report_only_count = 0
    for signal in signals:
        if len(tasks) >= max_tasks and signal.get("riskLevel") != "高":
            report_only_count += 1
            _save_signal(signal, "report_seed_only")
            continue
        if signal.get("queueType") in {"urgent_execution", "daily_operating_task", "weekly_review_task"}:
            payload = _task_payload(signal)
            gated = apply_evidence_gate_to_created_task(payload)
            task = module_task_service.create_task(gated)
            tasks.append(task)
            _save_signal(signal, "task_created", task.get("id"))
        else:
            candidate_count += 1
            _save_signal(signal, "candidate_only")

    return {
        "version": OPERATING_CADENCE_VERSION,
        "mode": "v12_4_upload_frequency_trend_window_agent_task_generation",
        "dataVersion": data_version,
        "cadence": cadence,
        "signalCount": len(signals),
        "createdTaskCount": len(tasks),
        "candidateCount": candidate_count,
        "reportSeedOnlyCount": report_only_count,
        "tasks": tasks,
        "topSignals": signals[:20],
        "rule": "V12.4：日报/周报不再只依赖已生成任务；趋势信号、候选任务、观察项和执行任务共同构成日报/周报基础。",
    }


def operating_cadence_summary(limit: int = 40) -> Dict[str, Any]:
    ensure_operating_cadence_tables()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM operating_cadence_signals ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    items = [loads(row["payload"]) for row in rows]
    by_status: Dict[str, int] = defaultdict(int)
    by_window: Dict[str, int] = defaultdict(int)
    by_report: Dict[str, int] = defaultdict(int)
    for item in items:
        by_status[str(item.get("status") or "unknown")] += 1
        by_window[str((item.get("window") or {}).get("windowType") or "unknown")] += 1
        by_report[str(item.get("reportTarget") or "unknown")] += 1
    return {
        "version": OPERATING_CADENCE_VERSION,
        "signalCount": len(items),
        "byStatus": dict(by_status),
        "byWindow": dict(by_window),
        "byReportTarget": dict(by_report),
        "dailyReportSeeds": [item for item in items if "日报" in str(item.get("reportTarget"))][:12],
        "weeklyReportSeeds": [item for item in items if "周报" in str(item.get("reportTarget"))][:12],
        "items": items,
        "rule": "日报/周报由执行任务、候选任务、趋势信号和观察项共同生成；上传频率越高，短周期波动权重越高。",
    }
