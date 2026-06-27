"""V12.4 operating rhythm task service.

Purpose:
    Ecommerce operation cannot wait for a single hard baseline to be crossed.
    Red-line rules remain hard safety gates, but day-to-day operations need a
    rhythm layer that looks at upload frequency, short/mid/long trend windows and
    metric volatility, then lets Agent-style judgment produce operating tasks.

This service reads the fact tables after import and creates structured SOP task
packages for:
    - daily operating review tasks;
    - opportunity capture tasks;
    - weekly review tasks;
    - evidence tasks when key proof is missing.

It deliberately does not replace the existing hard risk task chain.  It fills the
space between "no red-line warning" and "operator still needs to adjust today".
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Tuple

from src.repositories.sqlite_repository import connect, loads
from src.services import module_task_service
from src.services.metric_fact_store_service import ensure_metric_fact_tables
from src.services.report_alert_service import now_iso

OPERATING_RHYTHM_TASK_VERSION = "12.4.0"

WINDOWS = {
    "short": {"label": "3天短波动", "days": 3},
    "small": {"label": "7天小趋势", "days": 7},
    "medium_short": {"label": "14天中短趋势", "days": 14},
    "medium": {"label": "30天中趋势", "days": 30},
    "large": {"label": "90天大趋势", "days": 90},
}

METRIC_NAMES = {
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
    "organic_visitor_count": "自然流量访客数",
    "paid_visitor_count": "付费流量访客数",
    "gross_margin_rate": "毛利率",
    "refund_rate": "退款率",
    "refund_amount": "退款金额",
}


def _safe_float(value: Any) -> float | None:
    if value in {None, "", "未识别", "—"}:
        return None
    try:
        return float(str(value).replace("%", "").replace("¥", "").replace(",", ""))
    except (TypeError, ValueError):
        return None


def _date_key(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return "unknown"
    return text[:10]


def _parse_date(value: Any) -> date | None:
    text = _date_key(value)
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def _pct_change(first: float | None, latest: float | None) -> float | None:
    if first is None or latest is None:
        return None
    if abs(first) < 1e-9:
        return None
    return (latest - first) / abs(first)


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "未识别"
    return f"{value * 100:.1f}%"


def _metric_label(code: str) -> str:
    return METRIC_NAMES.get(code, code)


def _table_exists(conn: Any, table: str) -> bool:
    return bool(conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone())


def _latest_dates(limit: int = 12) -> List[str]:
    ensure_metric_fact_tables()
    with connect() as conn:
        if not _table_exists(conn, "product_metric_facts"):
            return []
        rows = conn.execute(
            """
            SELECT DISTINCT COALESCE(NULLIF(stat_date, ''), substr(updated_at, 1, 10), data_version) AS statDate
            FROM product_metric_facts
            WHERE COALESCE(NULLIF(stat_date, ''), data_version) IS NOT NULL
            ORDER BY statDate DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [str(row["statDate"]) for row in rows if row["statDate"]]


def upload_frequency_profile() -> Dict[str, Any]:
    dates = sorted({_date_key(item) for item in _latest_dates(30) if item and _date_key(item) != "unknown"})
    parsed = [_parse_date(item) for item in dates]
    parsed = [item for item in parsed if item]
    if len(parsed) < 2:
        return {
            "version": OPERATING_RHYTHM_TASK_VERSION,
            "uploadCount": len(parsed),
            "cadence": "insufficient",
            "sensitivity": "baseline",
            "shortWindowWeight": 1.0,
            "rule": "少于2个日期时，只能做事实展示和红线检查。",
        }
    span_days = max(1, (parsed[-1] - parsed[0]).days)
    avg_gap = span_days / max(1, len(parsed) - 1)
    if len(parsed) >= 3 and span_days <= 7:
        cadence = "high"
        sensitivity = "aggressive_short_cycle"
        short_weight = 0.65
    elif avg_gap <= 7:
        cadence = "medium"
        sensitivity = "weekly_operating_cycle"
        short_weight = 0.8
    elif avg_gap <= 14:
        cadence = "regular"
        sensitivity = "review_cycle"
        short_weight = 1.0
    else:
        cadence = "low"
        sensitivity = "summary_cycle"
        short_weight = 1.25
    return {
        "version": OPERATING_RHYTHM_TASK_VERSION,
        "uploadCount": len(parsed),
        "dateSpanDays": span_days,
        "avgUploadGapDays": round(avg_gap, 2),
        "cadence": cadence,
        "sensitivity": sensitivity,
        "shortWindowWeight": short_weight,
        "dates": [item.isoformat() for item in parsed],
        "rule": "上传频率越高，短周期趋势权重越高，经营调整任务越积极。",
    }


def _fetch_product_metric_points(limit_products: int = 80) -> List[Dict[str, Any]]:
    ensure_metric_fact_tables()
    wanted_metrics = tuple(METRIC_NAMES.keys())
    placeholders = ",".join("?" for _ in wanted_metrics)
    with connect() as conn:
        if not _table_exists(conn, "product_metric_facts"):
            return []
        rows = conn.execute(
            f"""
            SELECT *
            FROM product_metric_facts
            WHERE metric_code IN ({placeholders})
              AND (metric_scope IS NULL OR metric_scope = '' OR metric_scope = 'product')
            ORDER BY COALESCE(stat_date, updated_at) ASC, updated_at ASC
            LIMIT ?
            """,
            (*wanted_metrics, limit_products * len(wanted_metrics) * 8),
        ).fetchall()
    return [dict(row) for row in rows]


def _entity_key(row: Dict[str, Any]) -> Tuple[str, str, str]:
    store = str(row.get("store_code") or row.get("store_id") or row.get("store_name") or "GLOBAL")
    product = str(row.get("sku_code") or row.get("link_code") or row.get("spu_code") or row.get("product_id") or row.get("sku_id") or row.get("erp_product_code") or "UNKNOWN")
    name = str(row.get("product_id") or row.get("sku_id") or row.get("erp_product_code") or product)
    return store, product, name


def _build_entity_series(rows: Iterable[Dict[str, Any]]) -> Dict[Tuple[str, str, str], Dict[str, Any]]:
    entities: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    for row in rows:
        key = _entity_key(row)
        entity = entities.setdefault(
            key,
            {
                "storeCode": row.get("store_code"),
                "storeId": row.get("store_id"),
                "storeName": row.get("store_name"),
                "productId": row.get("product_id"),
                "skuId": row.get("sku_id"),
                "erpProductCode": row.get("erp_product_code"),
                "productLink": row.get("product_link"),
                "metricPoints": defaultdict(list),
                "sourceSheets": set(),
                "dataVersions": set(),
            },
        )
        metric = row.get("metric_code")
        value = _safe_float(row.get("metric_value"))
        if metric and value is not None:
            entity["metricPoints"][metric].append(
                {
                    "value": value,
                    "displayValue": row.get("display_value"),
                    "statDate": _date_key(row.get("stat_date") or row.get("updated_at") or row.get("data_version")),
                    "factId": row.get("fact_id"),
                    "sourceSheet": row.get("source_sheet"),
                    "sourceBlockId": row.get("source_block_id"),
                    "dataVersion": row.get("data_version"),
                }
            )
        if row.get("source_sheet"):
            entity["sourceSheets"].add(str(row.get("source_sheet")))
        if row.get("data_version"):
            entity["dataVersions"].add(str(row.get("data_version")))
    for entity in entities.values():
        entity["metricPoints"] = {metric: sorted(points, key=lambda item: item.get("statDate") or "") for metric, points in entity["metricPoints"].items()}
        entity["sourceSheets"] = sorted(entity["sourceSheets"])
        entity["dataVersions"] = sorted(entity["dataVersions"])
    return entities


def _first_latest(entity: Dict[str, Any], metric: str) -> Tuple[float | None, float | None, Dict[str, Any] | None, Dict[str, Any] | None]:
    points = entity.get("metricPoints", {}).get(metric) or []
    if not points:
        return None, None, None, None
    return points[0].get("value"), points[-1].get("value"), points[0], points[-1]


def _signal(entity: Dict[str, Any], metric: str) -> Dict[str, Any]:
    first, latest, first_point, latest_point = _first_latest(entity, metric)
    return {
        "metricCode": metric,
        "metricName": _metric_label(metric),
        "firstValue": first,
        "latestValue": latest,
        "changeRate": _pct_change(first, latest),
        "firstPoint": first_point,
        "latestPoint": latest_point,
    }


def _candidate_key(entity: Dict[str, Any], action_type: str, rhythm_window: str) -> str:
    return ":".join(
        [
            "v12_4",
            action_type,
            rhythm_window,
            str(entity.get("storeCode") or entity.get("storeId") or entity.get("storeName") or "GLOBAL"),
            str(entity.get("skuId") or entity.get("productId") or entity.get("erpProductCode") or entity.get("productLink") or "UNKNOWN"),
        ]
    )


def _ownership(entity: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "importedByUserId": "system",
        "importedByRoleId": "system",
        "ownerUserId": None,
        "assignedOperatorId": None,
        "reviewerId": None,
        "visibleUserIds": [],
        "visibleRoleIds": ["owner", "manager", "operator"],
        "rule": "V12.4：节奏任务默认对老板、总管、运营可见，后续按店铺归属收紧。",
    }


def _task_payload(entity: Dict[str, Any], candidate: Dict[str, Any], cadence: Dict[str, Any]) -> Dict[str, Any]:
    product_id = str(entity.get("productId") or entity.get("skuId") or entity.get("erpProductCode") or "经营对象")
    store_name = str(entity.get("storeName") or entity.get("storeId") or entity.get("storeCode") or "店铺")
    title = candidate["title"]
    priority = candidate.get("priority", "中")
    deadline = candidate.get("deadline", "24小时内")
    evidence = candidate.get("evidence", [])
    sop_steps = candidate.get("sopSteps", [])
    return {
        "taskGenerationMode": "v11_8_sop_package",
        "id": module_task_service.make_id("R"),
        "taskCard": {
            "title": title,
            "subtitle": candidate.get("domain", "经营节奏"),
            "priority": priority,
            "deadline": deadline,
            "reason": candidate.get("reason"),
        },
        "taskDetailReport": {
            "version": OPERATING_RHYTHM_TASK_VERSION,
            "title": title,
            "warningSummary": candidate.get("reason"),
            "rhythmWindow": candidate.get("rhythmWindow"),
            "rhythmWindowLabel": candidate.get("rhythmWindowLabel"),
            "uploadFrequency": cadence,
            "evidence": evidence,
            "agentJudgment": candidate.get("agentJudgment"),
            "sopSteps": sop_steps,
            "dataVersions": entity.get("dataVersions") or [],
            "sourceSheets": entity.get("sourceSheets") or [],
            "rule": "日报/周报不等正式任务产生，趋势信号和候选任务本身就是报告素材。",
        },
        "evidencePack": {
            "metricScope": "product",
            "requiredFactTables": ["product_metric_facts"],
            "evidence": evidence,
            "sourceSheets": entity.get("sourceSheets") or [],
            "dataVersions": entity.get("dataVersions") or [],
        },
        "sopSteps": sop_steps,
        "reviewMetrics": candidate.get("reviewMetrics") or ["补充截图或数据", "确认动作后指标变化", "回写复盘"],
        "completionGate": candidate.get("completionGate") or ["已完成数据复核", "已确认是否调整策略", "已提交结果截图或说明"],
        "failureThreshold": candidate.get("failureThreshold") or "24小时内未复核则升级给总管。",
        "agentJudgment": {
            "status": "v12_4_operating_rhythm_agent",
            "rhythmMode": candidate.get("rhythmMode"),
            "cadence": cadence.get("cadence"),
            "sensitivity": cadence.get("sensitivity"),
            "summary": candidate.get("agentJudgment"),
            "boundary": "红线硬控，波动区间交给Agent判断，证据闸门防止高风险误执行。",
        },
        "ownership": _ownership(entity),
        "priority": priority,
        "priorityLevel": "danger" if priority == "高" else "warning" if priority == "中" else "good",
        "deadline": deadline,
        "timeBucket": deadline,
        "sourceModule": "经营节奏Agent",
        "source": "经营节奏Agent",
        "sourceRoute": "business-actions",
        "productRoute": "business-products",
        "todoRoute": "business-actions",
        "entityType": "商品",
        "entityId": product_id,
        "productId": product_id,
        "store": store_name,
        "storeName": store_name,
        "storeIds": [str(entity.get("storeId") or entity.get("storeCode") or store_name)] if (entity.get("storeId") or entity.get("storeCode") or store_name) else [],
        "visibleStoreIds": [str(entity.get("storeId") or entity.get("storeCode") or store_name)] if (entity.get("storeId") or entity.get("storeCode") or store_name) else [],
        "taskLayer": "operator_execution",
        "taskType": candidate.get("taskType", "日常经营任务"),
        "queueType": candidate.get("queueType", "daily_operating_task"),
        "recapTarget": candidate.get("recapTarget", "日报"),
        "actionType": candidate.get("actionType", "经营复核"),
        "riskDomain": candidate.get("domain", "经营节奏"),
        "metricScope": "product",
        "sourceEvent": candidate.get("sourceEvent") or candidate.get("actionType"),
        "dedupeKey": candidate.get("dedupeKey") or _candidate_key(entity, candidate.get("actionType", "经营复核"), candidate.get("rhythmWindow", "small")),
        "judgmentTags": list(dict.fromkeys(["V12.4节奏任务", candidate.get("rhythmWindowLabel"), candidate.get("taskType"), candidate.get("rhythmMode")])),
        "reason": candidate.get("reason"),
        "sourceTrail": ["product_metric_facts", "upload_frequency_profile", "V12.4经营节奏Agent"],
    }


def _candidate(entity: Dict[str, Any], cadence: Dict[str, Any]) -> List[Dict[str, Any]]:
    weight = float(cadence.get("shortWindowWeight") or 1.0)
    inv = _signal(entity, "inventory_qty")
    sellable = _signal(entity, "sellable_days")
    pay = _signal(entity, "payment_amount")
    roi = _signal(entity, "roi")
    ad = _signal(entity, "ad_spend")
    conv = _signal(entity, "payment_conversion_rate")
    refund = _signal(entity, "refund_rate")
    candidates: List[Dict[str, Any]] = []

    inv_change = inv.get("changeRate")
    pay_change = pay.get("changeRate")
    roi_change = roi.get("changeRate")
    ad_change = ad.get("changeRate")
    conv_change = conv.get("changeRate")
    refund_change = refund.get("changeRate")
    latest_inv = inv.get("latestValue")
    latest_sellable = sellable.get("latestValue")

    def evidence(*signals: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [item for item in signals if item.get("latestValue") is not None]

    if latest_inv is not None and (latest_inv <= 0 or (inv_change is not None and inv_change <= -0.18 * weight) or (latest_sellable is not None and latest_sellable <= 7)):
        candidates.append({
            "title": "24小时内复核库存承接与补货动作",
            "taskType": "库存承接任务",
            "domain": "库存",
            "priority": "中" if latest_inv > 0 else "高",
            "deadline": "24小时内" if latest_inv > 0 else "12小时内",
            "queueType": "daily_operating_task",
            "recapTarget": "日报",
            "rhythmWindow": "small",
            "rhythmWindowLabel": WINDOWS["small"]["label"],
            "rhythmMode": "volatility_to_action",
            "actionType": "库存复核",
            "reason": f"库存最新值 {latest_inv:g}，库存变化 {_fmt_pct(inv_change)}，可售天数 {latest_sellable if latest_sellable is not None else '未识别'}，已进入短周期经营复核区。",
            "agentJudgment": "库存变化已影响销售承接，应先复核是否缺货、是否需要补货、是否要临时替换主推位。",
            "evidence": evidence(inv, sellable, pay),
            "sopSteps": ["12-24小时内核对该商品三端库存和在途库存。", "确认近3/7天支付金额是否仍在增长。", "库存不足时提交补货、限售或主推位替换建议。"],
            "reviewMetrics": ["库存数量", "可售天数", "支付金额", "支付件数"],
            "completionGate": ["库存安全线已确认", "是否补货或替换主推位已提交", "复核截图或数据已上传"],
        })

    if pay_change is not None and pay_change >= 0.10 * weight and (inv_change is not None and inv_change <= -0.08 * weight):
        candidates.append({
            "title": "24小时内承接增长商品，判断是否补货或放大流量",
            "taskType": "机会承接任务",
            "domain": "增长机会",
            "priority": "中",
            "deadline": "24小时内",
            "queueType": "daily_operating_task",
            "recapTarget": "日报",
            "rhythmWindow": "small",
            "rhythmWindowLabel": WINDOWS["small"]["label"],
            "rhythmMode": "opportunity_capture",
            "actionType": "机会承接",
            "reason": f"支付金额变化 {_fmt_pct(pay_change)}，库存变化 {_fmt_pct(inv_change)}，存在增长承接机会。",
            "agentJudgment": "销售增长同时库存下降，说明不是单纯风险，可能是可放大的机会，应复核是否加库存、加内容、加流量或调整主推位。",
            "evidence": evidence(pay, inv, roi, conv),
            "sopSteps": ["确认增长来自自然流量、付费流量还是活动承接。", "复核库存是否支撑未来3-7天销售。", "若ROI和转化可接受，提交放大流量或主推位承接建议。"],
        })

    if ad_change is not None and ad_change >= 0.15 * weight and (roi_change is not None and roi_change <= -0.05 * weight):
        candidates.append({
            "title": "12小时内复核广告投放效率和ROI变化",
            "taskType": "投放效率复核任务",
            "domain": "投产",
            "priority": "中",
            "deadline": "12小时内",
            "queueType": "daily_operating_task",
            "recapTarget": "日报",
            "rhythmWindow": "short",
            "rhythmWindowLabel": WINDOWS["short"]["label"],
            "rhythmMode": "spend_efficiency_review",
            "actionType": "投放复核",
            "reason": f"广告消耗变化 {_fmt_pct(ad_change)}，ROI变化 {_fmt_pct(roi_change)}，已进入投放效率复核区。",
            "agentJudgment": "广告消耗上升但ROI转弱，不必等ROI跌破红线，应当天复核计划、关键词、素材和人群。",
            "evidence": evidence(ad, roi, conv, pay),
            "sopSteps": ["12小时内检查广告计划、关键词、人群和素材消耗。", "对比同周期支付金额和转化率。", "若消耗继续上升且ROI未恢复，提交降预算或换素材建议。"],
        })

    if conv_change is not None and conv_change <= -0.08 * weight:
        candidates.append({
            "title": "24小时内排查转化率下滑原因",
            "taskType": "转化排查任务",
            "domain": "转化",
            "priority": "中",
            "deadline": "24小时内",
            "queueType": "daily_operating_task",
            "recapTarget": "日报",
            "rhythmWindow": "small",
            "rhythmWindowLabel": WINDOWS["small"]["label"],
            "rhythmMode": "conversion_review",
            "actionType": "转化排查",
            "reason": f"支付转化率变化 {_fmt_pct(conv_change)}，已经达到小趋势复核区。",
            "agentJudgment": "转化率下滑可能来自价格、素材、评价、库存或流量人群变化，应进入今日排查。",
            "evidence": evidence(conv, pay, roi, ad),
            "sopSteps": ["检查近7天主图、标题、价格、评价和库存状态。", "对比流量来源和广告计划变化。", "提交1个优先排查原因和处理动作。"],
        })

    if refund_change is not None and refund_change >= 0.20 * weight:
        candidates.append({
            "title": "24小时内复核退款率上升原因",
            "taskType": "售后复核任务",
            "domain": "售后",
            "priority": "中",
            "deadline": "24小时内",
            "queueType": "daily_operating_task",
            "recapTarget": "日报",
            "rhythmWindow": "small",
            "rhythmWindowLabel": WINDOWS["small"]["label"],
            "rhythmMode": "after_sales_review",
            "actionType": "售后复核",
            "reason": f"退款率变化 {_fmt_pct(refund_change)}，进入售后经营复核区。",
            "agentJudgment": "退款率抬头不一定已经红线，但会影响商品权重和后续投放，应及时复核退款原因。",
            "evidence": evidence(refund, pay, roi),
            "sopSteps": ["整理近7天退款原因TOP5。", "确认是否集中在尺码、质量、物流、描述不符或客服承诺。", "提交整改动作和复核时间。"],
        })

    return candidates


def generate_operating_rhythm_tasks(data_version: str | None = None, limit: int = 12, create_tasks: bool = True) -> Dict[str, Any]:
    rows = _fetch_product_metric_points(limit_products=160)
    entities = _build_entity_series(rows)
    cadence = upload_frequency_profile()
    candidates: List[Dict[str, Any]] = []
    created: List[Dict[str, Any]] = []
    for entity in entities.values():
        if len(entity.get("dataVersions") or []) < 2 and cadence.get("uploadCount", 0) < 2:
            continue
        entity_candidates = _candidate(entity, cadence)
        for candidate in entity_candidates:
            candidate["dedupeKey"] = _candidate_key(entity, candidate.get("actionType", "经营复核"), candidate.get("rhythmWindow", "small"))
            candidates.append({"entity": {key: value for key, value in entity.items() if key != "metricPoints"}, "candidate": candidate})
    priority_rank = {"高": 0, "中": 1, "低": 2}
    candidates.sort(key=lambda item: (priority_rank.get(item["candidate"].get("priority"), 9), item["candidate"].get("deadline", "99")))
    for item in candidates[:limit]:
        if not create_tasks:
            continue
        payload = _task_payload(item["entity"], item["candidate"], cadence)
        created.append(module_task_service.create_task(payload))
    return {
        "version": OPERATING_RHYTHM_TASK_VERSION,
        "mode": "upload_frequency_trend_window_agent_operating_tasks",
        "dataVersion": data_version,
        "uploadFrequency": cadence,
        "windowPolicy": WINDOWS,
        "entityCount": len(entities),
        "candidateCount": len(candidates),
        "createdTaskCount": len(created),
        "createdTasks": created,
        "candidatePreview": candidates[: min(limit, 8)],
        "rule": "红线任务仍由硬规则控制；3/7/14/30/90天波动进入Agent经营判断，形成日报/周报素材和日常经营任务。",
        "generatedAt": now_iso(),
    }
