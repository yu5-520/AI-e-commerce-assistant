"""V6.5 risk task service with permission-budget gates."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List
from uuid import uuid4

from src.repositories.sqlite_repository import connect, dumps, loads
from src.services import module_task_service
from src.services.high_risk_trend_gate_service import evaluate_high_risk_trend_gate
from src.services.indicator_rag_service import resolve_indicator_constraints
from src.services.permission_budget_service import resolve_permission_budget_gate

RISK_TASK_VERSION = "6.5.0"
RISK_RANK = {"高": 1, "中": 2, "低": 3}
POSITIVE_METRICS = {"roi", "traffic", "clicks", "ctr", "conversion_rate", "gross_margin", "sales_volume", "quantity", "revenue", "actual_paid", "good_review_rate"}
BLOCKER_METRICS = {"refund_rate", "refund_amount", "refund_count", "bad_review_rate"}


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


def _payload(row: Any) -> Dict[str, Any]:
    data = loads(row["payload"])
    return data if data else dict(row)


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
    return [_payload(row) for row in rows]


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
    data = loads(row["payload"])
    return {**data, "productId": product_id, "storeId": store_id or row["store_id"]}


def _dominant_risk(signals: Iterable[Dict[str, Any]]) -> str:
    risks = [str(item.get("riskLevel") or "低") for item in signals]
    return sorted(risks, key=lambda value: RISK_RANK.get(value, 9))[0] if risks else "低"


def _positive_count(signals: Iterable[Dict[str, Any]]) -> int:
    metrics = set()
    for item in signals:
        metric = str(item.get("sourceMetric") or "")
        direction = item.get("trendDirection")
        if metric in POSITIVE_METRICS and direction == "up":
            metrics.add(metric)
        if metric in BLOCKER_METRICS and direction == "down":
            metrics.add(metric)
    return len(metrics)


def _has_blocker(signals: Iterable[Dict[str, Any]]) -> bool:
    for item in signals:
        metric = str(item.get("sourceMetric") or "")
        direction = item.get("trendDirection")
        if metric in BLOCKER_METRICS and direction == "up":
            return True
        if metric in {"roi", "ctr", "conversion_rate", "gross_margin"} and direction == "down":
            return True
    return False


def _domain(signals: List[Dict[str, Any]], opportunity: bool = False) -> str:
    if opportunity:
        return "趋势"
    text = " ".join(f"{item.get('signalType')} {item.get('sourceMetric')}" for item in signals)
    if any(word in text for word in ["库存", "stock", "available_stock"]):
        return "库存"
    if any(word in text for word in ["ROI", "roi", "流量", "click", "ctr", "conversion"]):
        return "流量"
    if any(word in text for word in ["毛利", "gross_margin", "成本", "价格"]):
        return "利润"
    if any(word in text for word in ["售后", "退款", "差评", "refund", "bad_review"]):
        return "售后"
    return "趋势"


def _deadline(risk_level: str, constraints: Dict[str, Any]) -> str:
    if risk_level == "高":
        return "今日内"
    if risk_level == "中":
        return f"{(constraints.get('targets') or {}).get('observeDays') or 3}天内"
    return "本周内"


def _build_actions(risk_level: str, constraints: Dict[str, Any], gate: Dict[str, Any] | None, budget: Dict[str, Any]) -> List[str]:
    targets = constraints.get("targets") or {}
    actions: List[str] = []
    if targets.get("safetyStock") is not None:
        actions.append(f"库存不得低于 {targets['safetyStock']} 件安全线。")
    if targets.get("minRoi") is not None:
        actions.append(f"ROI 不得低于 {targets['minRoi']}。")
    if targets.get("minCtr") is not None:
        actions.append(f"点击率需保持在 {targets['minCtr'] * 100:.1f}% 以上。")
    if targets.get("minConversionRate") is not None:
        actions.append(f"转化率需保持在 {targets['minConversionRate'] * 100:.1f}% 以上。")
    if targets.get("minGrossMargin") is not None:
        actions.append(f"毛利率不得低于 {targets['minGrossMargin'] * 100:.1f}%。")
    if risk_level == "高":
        actions.append("高风险通过后也只能提交申请，不能自动执行。" if gate and gate.get("applicationAllowed") else "高风险未通过门控，只能复核。")
    if budget.get("suggestedTotalBudget"):
        chain = " → ".join(budget.get("approvalChain") or ["无需审批"])
        actions.append(f"建议申请总额度 {budget['suggestedTotalBudget']} 元；审批链路：{chain}。")
    return actions or ["缺少完整指标，转人工复核。"]


def _task_type(risk_level: str, domain: str, gate: Dict[str, Any] | None) -> str:
    if risk_level == "高":
        return "高风险投产申请任务" if gate and gate.get("applicationAllowed") else "高风险趋势门控复核任务"
    if risk_level == "中":
        return f"中风险{domain}指标修复任务"
    return "低风险趋势观察任务"


def _task_payload(product: Dict[str, Any], signals: List[Dict[str, Any]], data_version: str | None, risk_level: str, opportunity: bool, requester_role_id: str) -> Dict[str, Any]:
    domain = _domain(signals, opportunity)
    product_id = product.get("productId") or signals[0].get("productId")
    store_id = product.get("storeId") or signals[0].get("storeId")
    constraints = resolve_indicator_constraints(product, domain, risk_level, signals, data_version=data_version)
    gate = evaluate_high_risk_trend_gate(product, signals, constraints, data_version=data_version) if risk_level == "高" else None
    budget = resolve_permission_budget_gate(product=product, risk_level=risk_level, domain=domain, constraints=constraints, high_risk_gate=gate, requester_role_id=requester_role_id, data_version=data_version)
    application_allowed = bool(gate and gate.get("applicationAllowed"))
    task_type = _task_type(risk_level, domain, gate)
    suffix = "投产申请" if application_allowed else "趋势门控复核" if risk_level == "高" else f"{domain}指标修复" if risk_level == "中" else "趋势观察"
    actions = _build_actions(risk_level, constraints, gate, budget)
    return {
        "id": make_id("RISK"),
        "title": f"{product.get('title') or product_id} · {suffix}",
        "task": task_type,
        "taskType": task_type,
        "priority": risk_level,
        "deadline": _deadline(risk_level, constraints),
        "timeBucket": _deadline(risk_level, constraints),
        "source": "趋势中心",
        "sourceModule": "趋势中心",
        "sourceRoute": "trend-center",
        "productId": product_id,
        "entityId": product_id,
        "entityType": "商品",
        "store": product.get("storeName") or store_id or "未绑定店铺",
        "storeName": product.get("storeName"),
        "storeIds": [store_id] if store_id else [],
        "platform": product.get("platform") or "未知平台",
        "category": product.get("category") or "未分类",
        "riskDomain": domain,
        "actionType": "申请" if application_allowed else "复核" if risk_level == "高" else "修复" if risk_level == "中" else "观察",
        "taskLayer": "manager_dispatch" if risk_level == "高" else "operator_execution",
        "visibleRoleIds": ["owner", "manager", "finance"] if risk_level == "高" else ["manager", "operator"],
        "sourceEvent": f"V6.5:{data_version or 'latest'}:{product_id}:{domain}:{risk_level}:{budget.get('status')}",
        "riskGrade": risk_level,
        "riskPolicy": {"riskMode": budget.get("status"), "requiresRagMetrics": risk_level in {"中", "高"}, "requiresTrendGate": risk_level == "高", "requiresBudgetGate": True, "requiresApproval": budget.get("needsApproval"), "approvalChain": budget.get("approvalChain") or [], "rule": "账号额度决定任务是执行、申请还是升级审批。"},
        "ragIndicatorConstraints": constraints,
        "highRiskTrendGate": gate,
        "permissionBudgetGate": budget,
        "investmentApplicationAllowed": bool(application_allowed and budget.get("status") in {"application_allowed", "application_requires_escalation"}),
        "executionAllowed": bool(budget.get("executionAllowed")),
        "approvalChain": budget.get("approvalChain") or [],
        "suggestedAdBudget": budget.get("suggestedAdBudget"),
        "suggestedStockBudget": budget.get("suggestedStockBudget"),
        "suggestedTotalBudget": budget.get("suggestedTotalBudget"),
        "executionRequirements": actions,
        "judgmentTags": ["V6.5权限额度", f"{risk_level}风险", domain, budget.get("status")],
        "evidence": [{"type": "trend_signal", "title": item.get("signalType"), "metric": item.get("metricLabel") or item.get("sourceMetric"), "reason": item.get("reason"), "dataVersion": item.get("dataVersion")} for item in signals] + [{"type": "permission_budget", "title": "账号额度门控", "metric": f"申请额度 {budget.get('suggestedTotalBudget')} 元", "reason": budget.get("rule"), "dataVersion": data_version}],
        "reason": "；".join(item.get("reason") or item.get("signalType") or "趋势信号" for item in signals[:4]),
        "agentJudgment": {"status": "v6_5_permission_budget_task", "riskLevel": risk_level, "indicatorConstraints": constraints, "highRiskTrendGate": gate, "permissionBudgetGate": budget, "executionRequirements": actions, "boundary": "Agent 不能绕过账号额度和审批链路。"},
        "sourceTrail": ["报表中心", "趋势中心", "RAG指标门控", "高风险趋势门控", "权限额度门控", "风险分级任务"],
    }


def _save_plan(product_id: str, store_id: str | None, data_version: str | None, risk_level: str, task_type: str, task_id: str | None, status: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    ensure_risk_task_tables()
    plan = {"planId": make_id("RPLAN"), "productId": product_id, "storeId": store_id, "dataVersion": data_version, "riskLevel": risk_level, "taskType": task_type, "taskId": task_id, "status": status, "payload": payload, "createdAt": now_iso()}
    with connect() as conn:
        conn.execute("INSERT OR REPLACE INTO risk_task_plans_v6 (plan_id, product_id, store_id, data_version, risk_level, task_type, task_id, status, payload, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (plan["planId"], product_id, store_id, data_version, risk_level, task_type, task_id, status, dumps(plan), plan["createdAt"]))
        conn.commit()
    return plan


def generate_risk_tasks_for_signals(data_version: str | None = None, limit: int = 200, requester_role_id: str = "operator") -> Dict[str, Any]:
    ensure_risk_task_tables()
    signals = _load_signals(data_version=data_version, limit=limit)
    groups: Dict[tuple[str, str | None, str | None], List[Dict[str, Any]]] = defaultdict(list)
    for signal in signals:
        product_id = signal.get("productId")
        if product_id:
            groups[(str(product_id), signal.get("storeId"), signal.get("dataVersion") or data_version)].append(signal)
    tasks: List[Dict[str, Any]] = []
    plans: List[Dict[str, Any]] = []
    skipped = 0
    application_candidates = 0
    for (product_id, store_id, version), items in groups.items():
        dominant = _dominant_risk(items)
        opportunity = _positive_count(items) >= 4 and not _has_blocker(items)
        risk_level = "高" if opportunity else dominant
        candidates = [item for item in items if item.get("taskCandidate")]
        if not opportunity and risk_level == "低" and len(items) < 2:
            skipped += 1
            continue
        if not opportunity and risk_level in {"中", "高"} and not candidates:
            skipped += 1
            continue
        payload = _task_payload(_product_context(product_id, store_id), items, version, risk_level, opportunity, requester_role_id)
        if opportunity:
            application_candidates += 1
        task = module_task_service.create_task(payload)
        tasks.append(task)
        plans.append(_save_plan(product_id, store_id, version, payload["riskGrade"], payload["taskType"], task.get("id"), "created", {"task": task, "signals": items, "indicatorConstraints": payload.get("ragIndicatorConstraints"), "highRiskTrendGate": payload.get("highRiskTrendGate"), "permissionBudgetGate": payload.get("permissionBudgetGate")}))
    return {"version": RISK_TASK_VERSION, "mode": "permission_budget_task_generation", "dataVersion": data_version, "requesterRoleId": requester_role_id, "signalCount": len(signals), "groupCount": len(groups), "createdTaskCount": len(tasks), "skippedGroupCount": skipped, "investmentApplicationCandidateCount": application_candidates, "tasks": tasks, "plans": plans, "rule": "V6.5 接入账号额度与审批链路：运营提交申请，总管/老板按额度审批，高风险不能自动执行。"}


def risk_task_summary(limit: int = 30) -> Dict[str, Any]:
    ensure_risk_task_tables()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM risk_task_plans_v6 ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    plans = [loads(row["payload"]) for row in rows]
    by_level: Dict[str, int] = defaultdict(int)
    rag_matched = gate_passed = application_allowed = budget_checked = 0
    for plan in plans:
        by_level[str(plan.get("riskLevel") or "低")] += 1
        task = (plan.get("payload") or {}).get("task") or {}
        if (task.get("ragIndicatorConstraints") or {}).get("status") == "matched":
            rag_matched += 1
        if (task.get("highRiskTrendGate") or {}).get("gateStatus") == "passed":
            gate_passed += 1
        if task.get("investmentApplicationAllowed"):
            application_allowed += 1
        if task.get("permissionBudgetGate"):
            budget_checked += 1
    return {"version": RISK_TASK_VERSION, "total": len(plans), "byLevel": dict(by_level), "ragMatchedCount": rag_matched, "highRiskGatePassedCount": gate_passed, "investmentApplicationAllowedCount": application_allowed, "budgetCheckedCount": budget_checked, "latestPlans": plans}
