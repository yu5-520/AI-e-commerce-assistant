"""V14.3 Agent Judgment Station service.

Agent judges every product signal package under RAG operation-value boundaries.
Generated task snapshots must carry operation budget estimates and SOP evidence.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4

from src.repositories.sqlite_repository import connect, dumps, ensure_columns, loads
from src.services.llm_provider_service import generate_json
from src.services.operation_budget_service import estimate_operation_budget, reserve_budget_for_task
from src.services.rag_context_station_service import build_rag_context_snapshot, latest_rag_context
from src.services.signal_pool_service import list_signals, update_signal_status
from src.services.task_snapshot_station_service import create_task_snapshot

AGENT_JUDGMENT_STATION_VERSION = "14.3.0"
VALID_DECISIONS = {"create_task_snapshot", "manager_review_required", "observe_only", "ignore_noise", "data_gap_required", "merge_candidate"}
SNAPSHOT_DECISIONS = {"create_task_snapshot", "manager_review_required", "data_gap_required"}


def now_iso() -> str:
    return datetime.now().isoformat()


def make_judgment_id() -> str:
    return f"AJ-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:6].upper()}"


def ensure_agent_judgment_tables() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_judgments_v14 (
                judgment_id TEXT PRIMARY KEY,
                data_version TEXT,
                signal_id TEXT,
                entity_type TEXT,
                entity_id TEXT,
                decision TEXT NOT NULL,
                confidence REAL DEFAULT 0,
                status TEXT NOT NULL,
                rag_context_ref TEXT,
                payload TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        ensure_columns(conn, "agent_judgments_v14", {"data_version": "TEXT", "signal_id": "TEXT", "entity_type": "TEXT", "entity_id": "TEXT", "confidence": "REAL DEFAULT 0", "rag_context_ref": "TEXT", "updated_at": "TEXT"})
        conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_judgments_v14_version ON agent_judgments_v14(data_version, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_judgments_v14_decision ON agent_judgments_v14(decision, status, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_judgments_v14_signal ON agent_judgments_v14(signal_id, decision, status)")
        conn.commit()


def _row_to_judgment(row: Any) -> Dict[str, Any]:
    payload = loads(row["payload"])
    return {**payload, "judgmentId": row["judgment_id"], "dataVersion": row["data_version"], "signalId": row["signal_id"], "entityType": row["entity_type"], "entityId": row["entity_id"], "decision": row["decision"], "confidence": float(row["confidence"] or 0), "status": row["status"], "ragContextRef": row["rag_context_ref"], "createdAt": row["created_at"], "updatedAt": row["updated_at"]}


def _existing_judgment_for_signal(signal_id: str | None) -> Dict[str, Any] | None:
    if not signal_id:
        return None
    ensure_agent_judgment_tables()
    with connect() as conn:
        row = conn.execute("SELECT * FROM agent_judgments_v14 WHERE signal_id = ? ORDER BY created_at DESC LIMIT 1", (signal_id,)).fetchone()
    return _row_to_judgment(row) if row else None


def list_agent_judgments(data_version: str | None = None, status: str | None = None, limit: int = 200) -> Dict[str, Any]:
    ensure_agent_judgment_tables()
    clauses = []
    params: List[Any] = []
    if data_version:
        clauses.append("data_version = ?")
        params.append(data_version)
    if status:
        clauses.append("status = ?")
        params.append(status)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM agent_judgments_v14 {where} ORDER BY created_at DESC LIMIT ?", [*params, limit]).fetchall()
    items = [_row_to_judgment(row) for row in rows]
    by_decision: Dict[str, int] = defaultdict(int)
    by_status: Dict[str, int] = defaultdict(int)
    for item in items:
        by_decision[str(item.get("decision"))] += 1
        by_status[str(item.get("status"))] += 1
    return {"version": AGENT_JUDGMENT_STATION_VERSION, "dataVersion": data_version, "judgmentCount": len(items), "byDecision": dict(by_decision), "byStatus": dict(by_status), "judgments": items}


def _budget_task_type(signal: Dict[str, Any]) -> str:
    signal_type = str(signal.get("signalType") or "")
    metric = str(signal.get("metricCode") or "")
    if metric in {"roas", "roi", "adSpend"} or "roas" in signal_type:
        return "roas_increase" if str(signal.get("signalStrength")) in {"medium", "high"} else "roas_decrease"
    if signal_type.startswith("product_refund"):
        return "after_sales_check"
    if signal_type.startswith("product_inventory"):
        return "replenishment"
    if signal_type.startswith("data_gap"):
        return "data_gap_fix"
    return "detail_page_test"


def _budget_payload_from_signal(signal: Dict[str, Any], risk_level: str) -> Dict[str, Any]:
    metric = signal.get("productMetricSnapshot") or (signal.get("agentProductSnapshotPackage") or {}).get("metricSnapshot") or {}
    latest = (signal.get("trendWindows") or {}).get("windows") or {}
    return {
        "riskLevel": risk_level,
        "currentDailyAdSpend": metric.get("adSpend"),
        "adSpend": metric.get("adSpend"),
        "increaseRate": 0.15,
        "decreaseRate": 0.2,
        "testDays": 2,
        "observeDays": 2,
        "suggestedGoodsValue": metric.get("inventoryValue") or metric.get("paymentAmount") or 0,
        "expectedUnits": metric.get("paymentUnitCount") or metric.get("inventory") or 0,
        "unitDiscount": metric.get("unitDiscount") or 0,
        "unitSubsidy": metric.get("unitSubsidy") or 0,
        "campaignAdSpend": metric.get("campaignAdSpend") or 0,
        "trendWindows": latest,
    }


def _risk_from_signal(signal: Dict[str, Any]) -> tuple[str, str]:
    strength = str(signal.get("signalStrength") or "normal")
    signal_type = str(signal.get("signalType") or "")
    if strength == "high" or signal_type.startswith("redline_"):
        return "high", "高"
    if strength == "medium":
        return "medium", "中"
    return "low", "低"


def _decision_template(signal: Dict[str, Any], rag_context: Dict[str, Any]) -> Dict[str, Any]:
    signal_type = str(signal.get("signalType") or "")
    strength = str(signal.get("signalStrength") or "normal")
    metric = signal.get("metricCode") or "经营指标"
    entity_type = signal.get("entityType") or "product"
    entity_id = signal.get("entityId") or signal.get("productId") or signal.get("dataVersion") or "latest"
    risk_level, priority = _risk_from_signal(signal)
    if risk_level == "high":
        decision = "manager_review_required"
        task_type = "高风险经营复核任务"
        reason = "高风险信号必须进入总管审核，不受普通运营额度限制。"
    elif signal_type == "normal_state":
        decision = "observe_only"
        task_type = "正常状态观察留痕"
        reason = "全量信号包进入Agent判断；当前为正常状态，默认观察留痕。"
    elif signal_type.startswith("data_gap_"):
        decision = "data_gap_required"
        task_type = "数据补齐/归属复核任务"
        reason = "数据缺口影响后续判断，需要补齐或复核归属。"
    elif strength == "medium":
        decision = "create_task_snapshot"
        task_type = "经营波动复核任务"
        reason = "中风险信号具备运营操作价值，但必须校验运营额度。"
    else:
        decision = "observe_only"
        task_type = "观察信号"
        reason = "低风险信号进入观察池，避免任务泛滥。"
    deadline = "6小时内" if priority == "高" else "24小时内" if priority == "中" else "后台观察"
    budget_task_type = _budget_task_type(signal)
    operation_budget = estimate_operation_budget(budget_task_type, _budget_payload_from_signal(signal, risk_level))
    evidence = ["对应报表来源", "指标事实值", "运营补充说明"]
    if budget_task_type in {"roas_increase", "roas_decrease"}:
        evidence = ["投放后台截图", "ROAS变化", "广告消耗变化", "点击率/转化率变化"]
    elif budget_task_type == "campaign_apply":
        evidence = ["活动报名信息", "预计让利/补贴", "活动价截图", "毛利测算"]
    elif budget_task_type == "replenishment":
        evidence = ["库存截图", "可售天数", "供应链反馈", "补货建议"]
    task_plan = {"title": f"{task_type}｜{entity_id}", "subtitle": signal_type, "entityType": entity_type, "entityId": entity_id, "productId": signal.get("productId"), "storeId": signal.get("storeId"), "verticalCategory": signal.get("verticalCategory"), "taskType": budget_task_type, "actionType": "agent_budgeted_operation", "priority": priority, "riskLevel": risk_level, "deadline": deadline, "riskDomain": metric, "operationBudget": operation_budget, "sopSteps": [f"{deadline}复核 {metric} 信号、垂直类目和原始报表证据。", "根据RAG类目基线、ROAS规则、任务额度和历史复盘确认处理动作。", "如果涉及ROAS增投/降投，必须提交预算公式、预估额度、止损线和复盘时间。", "提交截图、数据口径、处理结论和需要复核的指标。"], "evidenceRequirements": evidence, "reviewMetrics": ["ROAS", "广告消耗", "GMV/支付金额", "点击率", "转化率", "退款率", "毛利率", "库存"], "needManagerReview": decision == "manager_review_required", "reason": reason}
    return {"decision": decision, "confidence": 0.8 if decision in SNAPSHOT_DECISIONS else 0.62, "reason": reason, "taskPlan": task_plan, "operationBudget": operation_budget, "evidenceRequirements": evidence, "reviewMetrics": task_plan["reviewMetrics"], "riskBoundary": ["Agent outputs structured judgment and budget estimate only.", "System validates budget, reserves quota, and controls lifecycle.", "High-risk signals enter manager review and cannot be ignored by ordinary quota."], "ragContextApplied": bool(rag_context)}


def _normalize_llm_output(output: Dict[str, Any], fallback: Dict[str, Any]) -> Dict[str, Any]:
    decision = output.get("decision")
    if decision not in VALID_DECISIONS:
        return fallback
    merged = {**fallback, **{key: value for key, value in output.items() if value is not None}}
    merged["decision"] = decision
    try:
        merged["confidence"] = max(0.0, min(1.0, float(merged.get("confidence") or fallback.get("confidence") or 0)))
    except Exception:
        merged["confidence"] = fallback.get("confidence") or 0.5
    if not isinstance(merged.get("taskPlan"), dict):
        merged["taskPlan"] = fallback.get("taskPlan") or {}
    if not isinstance(merged.get("operationBudget"), dict):
        merged["operationBudget"] = (merged.get("taskPlan") or {}).get("operationBudget") or fallback.get("operationBudget") or {}
    if not isinstance(merged.get("evidenceRequirements"), list):
        merged["evidenceRequirements"] = fallback.get("evidenceRequirements") or []
    if not isinstance(merged.get("reviewMetrics"), list):
        merged["reviewMetrics"] = fallback.get("reviewMetrics") or []
    merged["taskPlan"]["operationBudget"] = merged.get("operationBudget")
    return merged


def _judge_signal(signal: Dict[str, Any], rag_context: Dict[str, Any]) -> Dict[str, Any]:
    fallback = _decision_template(signal, rag_context)
    llm_result = generate_json(prompt_name="v143_operation_value_budget_judgment", payload={"signalPackage": signal, "ragContext": rag_context, "fallbackDecision": fallback, "interfaceBoundary": "Agent judges operation value and budget estimate; code controls budget reservation and lifecycle."}, expected_keys=["decision", "confidence", "reason", "taskPlan", "operationBudget"], agent_name="V14.3 Operation Value Agent", schema_name="v143_agent_budget_judgment")
    output = llm_result.get("output") or {}
    judgment = _normalize_llm_output(output, fallback)
    judgment["llm"] = {"provider": llm_result.get("provider"), "model": llm_result.get("model"), "status": llm_result.get("status"), "fallbackUsed": llm_result.get("fallbackUsed"), "trace": llm_result.get("trace")}
    return judgment


def _signal_status_for_decision(decision: str) -> str:
    if decision in SNAPSHOT_DECISIONS:
        return "judged_pending_snapshot"
    if decision == "ignore_noise":
        return "ignored_noise"
    if decision == "merge_candidate":
        return "merge_candidate"
    return "observed_only"


def _save_judgment(signal: Dict[str, Any], rag_context: Dict[str, Any], judgment: Dict[str, Any]) -> Dict[str, Any]:
    existing = _existing_judgment_for_signal(signal.get("signalId"))
    if existing:
        return {**existing, "idempotentHit": True}
    ensure_agent_judgment_tables()
    judgment_id = make_judgment_id()
    created_at = now_iso()
    status = "pending_task_snapshot" if judgment.get("decision") in SNAPSHOT_DECISIONS else "judgment_recorded"
    payload = {"version": AGENT_JUDGMENT_STATION_VERSION, "judgmentId": judgment_id, "stationId": "agent_judgment_station", "dataVersion": signal.get("dataVersion"), "signalId": signal.get("signalId"), "entityType": signal.get("entityType"), "entityId": signal.get("entityId"), "signal": signal, "ragContextRef": rag_context.get("ragContextRef") or rag_context.get("outputRef"), "ragContext": rag_context, "decision": judgment.get("decision"), "confidence": judgment.get("confidence") or 0, "reason": judgment.get("reason"), "taskPlan": judgment.get("taskPlan") or {}, "operationBudget": judgment.get("operationBudget") or {}, "evidenceRequirements": judgment.get("evidenceRequirements") or [], "reviewMetrics": judgment.get("reviewMetrics") or [], "riskBoundary": judgment.get("riskBoundary") or [], "agentJudgment": judgment, "directInterfaceControlAllowed": False, "rule": "V14.3 Agent judgment is idempotent by signalId and carries operation budget."}
    with connect() as conn:
        conn.execute("""
            INSERT INTO agent_judgments_v14 (judgment_id, data_version, signal_id, entity_type, entity_id, decision, confidence, status, rag_context_ref, payload, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (judgment_id, signal.get("dataVersion"), signal.get("signalId"), signal.get("entityType"), signal.get("entityId"), judgment.get("decision"), float(judgment.get("confidence") or 0), status, payload["ragContextRef"], dumps(payload), created_at, created_at))
        conn.commit()
        row = conn.execute("SELECT * FROM agent_judgments_v14 WHERE judgment_id = ?", (judgment_id,)).fetchone()
    update_signal_status(signal.get("signalId"), _signal_status_for_decision(str(judgment.get("decision") or "")), {"agentJudgmentId": judgment_id, "decision": judgment.get("decision"), "operationBudget": judgment.get("operationBudget")})
    return _row_to_judgment(row)


def run_agent_judgment_station(data_version: str | None = None, *, rag_context_ref: str | None = None, max_signals: int = 32) -> Dict[str, Any]:
    ensure_agent_judgment_tables()
    rag_context = latest_rag_context(data_version)
    if not rag_context:
        rag_context = build_rag_context_snapshot(data_version=data_version)
    signals = (list_signals(data_version=data_version, status="pending_rag_agent", limit=max_signals).get("signals") or [])[:max_signals]
    judgments = [_save_judgment(signal, rag_context, _judge_signal(signal, rag_context)) for signal in signals]
    by_decision: Dict[str, int] = defaultdict(int)
    for item in judgments:
        by_decision[str(item.get("decision"))] += 1
    ref = f"agent_judgment:{data_version or 'latest'}"
    return {"version": AGENT_JUDGMENT_STATION_VERSION, "mode": "rag_operation_value_budget_agent_judgment", "dataVersion": data_version, "ragContextRef": rag_context_ref or rag_context.get("ragContextRef") or rag_context.get("outputRef"), "agentJudgmentRef": ref, "outputRef": ref, "signalCount": len(signals), "judgmentCount": len(judgments), "pendingTaskSnapshotCount": sum(1 for item in judgments if item.get("decision") in SNAPSHOT_DECISIONS), "byDecision": dict(by_decision), "judgments": judgments, "rule": "V14.3 Agent judges full signal packages under RAG operation-value and budget boundaries."}


def materialize_task_snapshots_from_judgments(data_version: str | None = None, *, created_by: str | None = None, limit: int = 50) -> Dict[str, Any]:
    result = list_agent_judgments(data_version=data_version, status="pending_task_snapshot", limit=limit)
    snapshots: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    budget_ledgers: List[Dict[str, Any]] = []
    for item in result.get("judgments") or []:
        decision = item.get("decision")
        if decision not in SNAPSHOT_DECISIONS:
            skipped.append({"judgmentId": item.get("judgmentId"), "reason": "decision_not_for_task_snapshot", "decision": decision})
            continue
        plan = item.get("taskPlan") or {}
        plan["operationBudget"] = item.get("operationBudget") or plan.get("operationBudget") or {}
        snapshot = create_task_snapshot({"dataVersion": item.get("dataVersion"), "decision": decision, "confidence": item.get("confidence"), "entityType": item.get("entityType"), "entityId": item.get("entityId"), "productId": plan.get("productId") or (item.get("signal") or {}).get("productId"), "storeId": plan.get("storeId") or (item.get("signal") or {}).get("storeId"), "riskLevel": plan.get("riskLevel") or (item.get("operationBudget") or {}).get("riskLevel"), "operationBudget": item.get("operationBudget") or {}, "signalRef": item.get("signalId"), "ragContext": item.get("ragContext") or {}, "agentJudgment": item.get("agentJudgment") or {}, "taskPlan": plan, "evidenceRequirements": item.get("evidenceRequirements") or [], "systemFacts": {"signal": item.get("signal") or {}, "judgmentId": item.get("judgmentId"), "operationBudget": item.get("operationBudget") or {}}, "source": "agent_judgment_station"}, created_by=created_by)
        snapshots.append(snapshot)
        budget_ledgers.append(reserve_budget_for_task({**snapshot, "operationBudget": item.get("operationBudget") or {}, "riskLevel": plan.get("riskLevel") or (item.get("operationBudget") or {}).get("riskLevel"), "storeId": plan.get("storeId") or (item.get("signal") or {}).get("storeId"), "productId": plan.get("productId") or (item.get("signal") or {}).get("productId")}, user_id=created_by))
        with connect() as conn:
            payload = dict(item)
            payload["taskSnapshotId"] = snapshot.get("taskSnapshotId")
            payload["budgetLedger"] = budget_ledgers[-1]
            conn.execute("UPDATE agent_judgments_v14 SET status = ?, payload = ?, updated_at = ? WHERE judgment_id = ?", ("task_snapshot_created", dumps(payload), now_iso(), item.get("judgmentId")))
            conn.commit()
        update_signal_status(item.get("signalId"), "task_snapshot_created", {"taskSnapshotId": snapshot.get("taskSnapshotId"), "judgmentId": item.get("judgmentId"), "budgetLedger": budget_ledgers[-1]})
    return {"version": AGENT_JUDGMENT_STATION_VERSION, "dataVersion": data_version, "taskSnapshotCount": len(snapshots), "snapshots": snapshots, "budgetLedgers": budget_ledgers, "skipped": skipped, "outputRef": f"task_snapshot:{data_version or 'latest'}", "rule": "V14.3 snapshots are materialized immediately with budget reservation."}
