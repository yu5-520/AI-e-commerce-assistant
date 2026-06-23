"""V6.3 risk-graded task generation service with RAG indicator constraints.

V6.2 introduced risk-graded task generation. V6.3 adds the company rule/RAG
indicator layer: medium/high-risk tasks must carry concrete boundaries such as
stock safety lines, ROI floors, CTR/CVR ranges, gross-margin floors, and stop or
review gates. High-risk tasks remain review-only until historical trend and
permission gates are added.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List
from uuid import uuid4

from src.repositories.sqlite_repository import connect, dumps, loads
from src.services import module_task_service
from src.services.indicator_rag_service import resolve_indicator_constraints

RISK_TASK_VERSION = "6.3.0"
RISK_RANK = {"高": 1, "中": 2, "低": 3}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}".upper()


def ensure_risk_task_tables() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS risk_task_plans_v6 (
                plan_id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                store_id TEXT,
                data_version TEXT,
                risk_level TEXT NOT NULL,
                task_type TEXT NOT NULL,
                task_id TEXT,
                status TEXT NOT NULL,
                payload TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_risk_task_plans_product_v6 ON risk_task_plans_v6(product_id, store_id, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_risk_task_plans_version_v6 ON risk_task_plans_v6(data_version, created_at)")
        conn.commit()


def _signal_payload(row: Any) -> Dict[str, Any]:
    payload = loads(row["payload"])
    if payload:
        return payload
    return dict(row)


def _load_signals(data_version: str | None = None, limit: int = 200) -> List[Dict[str, Any]]:
    ensure_risk_task_tables()
    if data_version:
        query = "SELECT * FROM business_signals_v6 WHERE data_version = ? ORDER BY created_at DESC LIMIT ?"
        params: tuple[Any, ...] = (data_version, limit)
    else:
        query = "SELECT * FROM business_signals_v6 ORDER BY created_at DESC LIMIT ?"
        params = (limit,)
    with connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [_signal_payload(row) for row in rows]


def _product_context(product_id: str, store_id: str | None = None) -> Dict[str, Any]:
    if store_id:
        query = "SELECT * FROM product_master_v6 WHERE product_id = ? AND (store_id = ? OR store_id IS NULL) LIMIT 1"
        params: tuple[Any, ...] = (product_id, store_id)
    else:
        query = "SELECT * FROM product_master_v6 WHERE product_id = ? LIMIT 1"
        params = (product_id,)
    with connect() as conn:
        row = conn.execute(query, params).fetchone()
    if not row:
        return {"productId": product_id, "storeId": store_id, "title": f"商品 {product_id}"}
    payload = loads(row["payload"])
    return {**payload, "productId": product_id, "storeId": store_id or row["store_id"]}


def _dominant_risk(signals: Iterable[Dict[str, Any]]) -> str:
    risks = [str(item.get("riskLevel") or "低") for item in signals]
    return sorted(risks, key=lambda item: RISK_RANK.get(item, 9))[0] if risks else "低"


def _risk_domain(signals: List[Dict[str, Any]]) -> str:
    text = " ".join(str(item.get("signalType") or "") + " " + str(item.get("sourceMetric") or "") for item in signals)
    if any(word in text for word in ["库存", "stock", "available_stock"]):
        return "库存"
    if any(word in text for word in ["ROI", "roi", "流量", "click", "ctr", "conversion"]):
        return "流量"
    if any(word in text for word in ["毛利", "gross_margin", "成本", "价格"]):
        return "利润"
    if any(word in text for word in ["售后", "退款", "差评", "refund", "bad_review"]):
        return "售后"
    return "趋势"


def _task_type(risk_level: str, domain: str, signals: List[Dict[str, Any]]) -> str:
    signal_names = " ".join(str(item.get("signalType") or "") for item in signals)
    if risk_level == "高":
        return "高风险指标门控复核任务"
    if "库存" in domain:
        return "中风险库存指标任务" if risk_level == "中" else "低风险库存趋势观察"
    if "流量" in domain:
        return "中风险 ROI / 流量指标修复任务" if risk_level == "中" else "低风险流量趋势观察"
    if "售后" in domain:
        return "中风险售后指标排查任务" if risk_level == "中" else "低风险售后观察"
    if "增长信号" in signal_names and risk_level == "低":
        return "低风险趋势观察任务"
    return "中风险经营信号指标复核任务" if risk_level == "中" else "低风险数据观察任务"


def _deadline_for(risk_level: str, constraints: Dict[str, Any] | None = None) -> str:
    if risk_level == "高":
        return "今日内"
    if risk_level == "中":
        days = (constraints or {}).get("targets", {}).get("observeDays") or 3
        return f"{days}天内"
    return "本周内"


def _task_layer_for(risk_level: str, domain: str) -> str:
    if risk_level == "高":
        return "manager_dispatch"
    if domain in {"利润", "流量", "售后"}:
        return "finance_check" if domain == "利润" else "operator_execution"
    return "operator_execution"


def _visible_roles_for(risk_level: str, domain: str) -> List[str]:
    if risk_level == "高":
        return ["owner", "manager", "finance"]
    if domain == "利润":
        return ["manager", "finance"]
    return ["manager", "operator"]


def _execution_policy(risk_level: str, signals: List[Dict[str, Any]], constraints: Dict[str, Any]) -> Dict[str, Any]:
    metrics = [item.get("metricLabel") or item.get("sourceMetric") for item in signals]
    matched = constraints.get("status") == "matched"
    if risk_level == "低":
        return {
            "riskMode": "direct_generation",
            "allowedAction": "生成观察 / 排查任务",
            "requiresRagMetrics": False,
            "ragMatched": matched,
            "requiresApproval": False,
            "rule": "低风险任务只消耗排查与复盘人力，不直接扩大库存或预算，允许 Agent 直接生成任务内容。",
        }
    if risk_level == "中":
        return {
            "riskMode": "rag_metric_bounded_execution" if matched else "metric_missing_review",
            "allowedAction": "生成带RAG指标边界的修复 / 观察任务" if matched else "指标缺失时只能生成人工复核任务",
            "requiresRagMetrics": True,
            "ragMatched": matched,
            "requiresApproval": False,
            "metricPlaceholders": metrics,
            "indicatorLines": constraints.get("executionLines") or [],
            "rule": "中风险任务必须带库存、ROI、点击率、转化率、毛利率等具体指标边界；缺失指标时不允许输出执行型动作。",
        }
    return {
        "riskMode": "rag_review_gate_only",
        "allowedAction": "只能生成复核 / 审批候选，不允许直接加库存、加投放或扩大预算",
        "requiresRagMetrics": True,
        "ragMatched": matched,
        "requiresApproval": True,
        "metricPlaceholders": metrics,
        "indicatorLines": constraints.get("executionLines") or [],
        "trendGate": constraints.get("trendGate") or {},
        "rule": "高风险任务涉及扩大投产，必须通过 RAG 指标和历史趋势门控；V6.3 只生成复核候选。",
    }


def _indicator_actions(risk_level: str, domain: str, constraints: Dict[str, Any]) -> List[str]:
    targets = constraints.get("targets") or {}
    lines = constraints.get("executionLines") or []
    actions: List[str] = []
    if domain == "库存" and targets.get("safetyStock") is not None:
        actions.append(f"在{targets.get('observeDays') or 3}天内确认补货时间，补货后库存不得低于 {targets['safetyStock']} 件安全线。")
    if targets.get("minRoi") is not None:
        actions.append(f"ROI 不得低于 {targets['minRoi']}，连续低于红线则转降投/复核。")
    if targets.get("minCtr") is not None:
        actions.append(f"点击率需保持在 {targets['minCtr'] * 100:.1f}% 以上。")
    if targets.get("minConversionRate") is not None:
        actions.append(f"转化率需保持在 {targets['minConversionRate'] * 100:.1f}% 以上。")
    if targets.get("minGrossMargin") is not None:
        actions.append(f"毛利率不得低于 {targets['minGrossMargin'] * 100:.1f}%，低于红线禁止继续加投。")
    if targets.get("maxRefundRate") is not None:
        actions.append(f"退款率不得高于 {targets['maxRefundRate'] * 100:.1f}%。")
    if targets.get("maxBadReviewRate") is not None:
        actions.append(f"差评率不得高于 {targets['maxBadReviewRate'] * 100:.1f}%。")
    if risk_level == "高":
        gate = constraints.get("trendGate") or {}
        actions.append(f"高风险动作仅进入复核：当前稳定向好指标 {gate.get('positiveMetricCount', 0)} 项，需满足公司规则后才可申请扩大投产。")
    return actions or lines or [constraints.get("gateConclusion") or "缺少可执行指标，转人工复核。"]


def _task_payload(product: Dict[str, Any], signals: List[Dict[str, Any]], data_version: str | None) -> Dict[str, Any]:
    risk_level = _dominant_risk(signals)
    domain = _risk_domain(signals)
    task_type = _task_type(risk_level, domain, signals)
    product_id = product.get("productId") or signals[0].get("productId")
    store_id = product.get("storeId") or signals[0].get("storeId")
    signal_labels = [f"{item.get('signalType')} / {item.get('metricLabel') or item.get('sourceMetric')} / {item.get('trendDirection')}" for item in signals]
    constraints = resolve_indicator_constraints(product, domain, risk_level, signals, data_version=data_version)
    policy = _execution_policy(risk_level, signals, constraints)
    deadline = _deadline_for(risk_level, constraints)
    if risk_level == "高":
        title = f"{product.get('title') or product_id} · 高风险指标门控复核"
    elif risk_level == "中":
        title = f"{product.get('title') or product_id} · {domain}指标修复任务"
    else:
        title = f"{product.get('title') or product_id} · 趋势观察任务"
    return {
        "id": make_id("RISK"),
        "title": title,
        "task": task_type,
        "taskType": task_type,
        "priority": risk_level,
        "deadline": deadline,
        "timeBucket": deadline,
        "source": "趋势中心",
        "sourceModule": "趋势中心",
        "sourceRoute": "trend-center",
        "productRoute": "trend-center",
        "productId": product_id,
        "entityId": product_id,
        "entityType": "商品",
        "store": product.get("storeName") or store_id or "未绑定店铺",
        "storeName": product.get("storeName"),
        "storeIds": [store_id] if store_id else [],
        "platform": product.get("platform") or "未知平台",
        "category": product.get("category") or "未分类",
        "riskDomain": domain,
        "actionType": "复核" if risk_level == "高" else "修复" if risk_level == "中" else "观察",
        "taskLayer": _task_layer_for(risk_level, domain),
        "visibleRoleIds": _visible_roles_for(risk_level, domain),
        "sourceEvent": f"V6.3:{data_version or 'latest'}:{product_id}:{domain}:{risk_level}",
        "riskGrade": risk_level,
        "riskPolicy": policy,
        "ragIndicatorConstraints": constraints,
        "executionRequirements": _indicator_actions(risk_level, domain, constraints),
        "judgmentTags": ["V6.3RAG指标", f"{risk_level}风险", domain, *[str(item.get("signalType")) for item in signals[:3]]],
        "evidence": [
            {
                "type": "trend_signal",
                "title": item.get("signalType"),
                "metric": item.get("metricLabel") or item.get("sourceMetric"),
                "changeRate": item.get("changeRate"),
                "reason": item.get("reason"),
                "dataVersion": item.get("dataVersion"),
            }
            for item in signals
        ] + [
            {
                "type": "rag_indicator_rule",
                "title": source.get("sourceTitle") or source.get("ruleId"),
                "metric": source.get("formula"),
                "reason": source.get("summary"),
                "dataVersion": data_version,
            }
            for source in constraints.get("ragSources", [])
        ],
        "reason": "；".join(item.get("reason") or item.get("signalType") or "趋势信号" for item in signals[:4]),
        "agentJudgment": {
            "status": "v6_3_rag_indicator_task",
            "riskLevel": risk_level,
            "summary": f"系统基于 {len(signals)} 条经营信号和 {len(constraints.get('ruleIds') or [])} 条RAG指标规则生成{risk_level}风险任务。",
            "policy": policy,
            "signals": signal_labels,
            "indicatorConstraints": constraints,
            "executionRequirements": _indicator_actions(risk_level, domain, constraints),
            "boundary": "Agent 不允许自造中高风险指标；缺少RAG指标时只能生成复核或数据补全任务。",
            "nextVersionBoundary": "V6.4 将接入高风险历史趋势门控：7天/30天窗口至少4项稳定向好，才允许生成扩大投产申请。",
        },
        "sourceTrail": ["报表中心", "趋势中心", "RAG指标门控", "风险分级任务"],
    }


def _save_plan(product_id: str, store_id: str | None, data_version: str | None, risk_level: str, task_type: str, task_id: str | None, status: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    ensure_risk_task_tables()
    plan = {
        "planId": make_id("RPLAN"),
        "productId": product_id,
        "storeId": store_id,
        "dataVersion": data_version,
        "riskLevel": risk_level,
        "taskType": task_type,
        "taskId": task_id,
        "status": status,
        "payload": payload,
        "createdAt": now_iso(),
    }
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO risk_task_plans_v6 (plan_id, product_id, store_id, data_version, risk_level, task_type, task_id, status, payload, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (plan["planId"], product_id, store_id, data_version, risk_level, task_type, task_id, status, dumps(plan), plan["createdAt"]),
        )
        conn.commit()
    return plan


def generate_risk_tasks_for_signals(data_version: str | None = None, limit: int = 200) -> Dict[str, Any]:
    """Generate low / medium / high risk tasks from V6.1 business signals with V6.3 indicators."""
    ensure_risk_task_tables()
    signals = _load_signals(data_version=data_version, limit=limit)
    groups: Dict[tuple[str, str | None, str | None], List[Dict[str, Any]]] = defaultdict(list)
    for signal in signals:
        product_id = signal.get("productId")
        if not product_id:
            continue
        key = (str(product_id), signal.get("storeId"), signal.get("dataVersion") or data_version)
        groups[key].append(signal)
    created_tasks: List[Dict[str, Any]] = []
    plans: List[Dict[str, Any]] = []
    skipped = 0
    for (product_id, store_id, version), items in groups.items():
        dominant = _dominant_risk(items)
        task_candidates = [item for item in items if item.get("taskCandidate")]
        if dominant == "低" and len(items) < 2:
            skipped += 1
            continue
        if dominant in {"中", "高"} and not task_candidates:
            skipped += 1
            continue
        product = _product_context(product_id, store_id)
        payload = _task_payload(product, items, version)
        task = module_task_service.create_task(payload)
        created_tasks.append(task)
        plans.append(_save_plan(product_id, store_id, version, payload["riskGrade"], payload["taskType"], task.get("id"), "created", {"task": task, "signals": items, "indicatorConstraints": payload.get("ragIndicatorConstraints")}))
    return {
        "version": RISK_TASK_VERSION,
        "mode": "rag_indicator_risk_task_generation",
        "dataVersion": data_version,
        "signalCount": len(signals),
        "groupCount": len(groups),
        "createdTaskCount": len(created_tasks),
        "skippedGroupCount": skipped,
        "tasks": created_tasks,
        "plans": plans,
        "rule": "低风险可直接生成；中风险必须带RAG指标边界；高风险只生成复核/审批候选，不直接扩大投产。",
    }


def risk_task_summary(limit: int = 30) -> Dict[str, Any]:
    ensure_risk_task_tables()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM risk_task_plans_v6 ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    plans = [loads(row["payload"]) for row in rows]
    by_level: Dict[str, int] = defaultdict(int)
    rag_matched = 0
    for plan in plans:
        by_level[str(plan.get("riskLevel") or "低")] += 1
        task = (plan.get("payload") or {}).get("task") or {}
        if (task.get("ragIndicatorConstraints") or {}).get("status") == "matched":
            rag_matched += 1
    return {
        "version": RISK_TASK_VERSION,
        "total": len(plans),
        "byLevel": dict(by_level),
        "ragMatchedCount": rag_matched,
        "latestPlans": plans,
    }
