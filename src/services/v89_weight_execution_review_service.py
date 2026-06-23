"""V8.9 weight execution feedback and review service.

V8.8 approval only unlocks a task group for the later execution layer. V8.9
records execution feedback and creates an after-action review. This version is a
closed-loop record layer: it stores what was actually done, the evidence, the
before/after result, and the next decision. It still does not directly call any
platform API to change spend, remove products, or alter user permissions.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from src.core.context import UserContext
from src.repositories.sqlite_repository import connect, dumps, loads
from src.services.v88_weight_approval_service import ensure_weight_approval_tables, generate_weight_approvals

V89_EXECUTION_VERSION = "8.9.0"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}".upper()


def ensure_weight_execution_tables() -> None:
    ensure_weight_approval_tables()
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS weight_execution_feedback_v8 (
                execution_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                org_id TEXT NOT NULL,
                approval_id TEXT NOT NULL,
                task_group_id TEXT NOT NULL,
                object_type TEXT NOT NULL,
                object_id TEXT NOT NULL,
                object_name TEXT,
                group_type TEXT,
                group_name TEXT,
                execution_status TEXT NOT NULL,
                execution_gate TEXT NOT NULL,
                planned_actions TEXT,
                actual_actions TEXT,
                before_state TEXT,
                after_state TEXT,
                result_metrics TEXT,
                evidence_refs TEXT,
                executor_id TEXT,
                feedback_note TEXT,
                payload TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS weight_execution_reviews_v8 (
                review_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                org_id TEXT NOT NULL,
                execution_id TEXT NOT NULL,
                approval_id TEXT NOT NULL,
                task_group_id TEXT NOT NULL,
                object_type TEXT NOT NULL,
                object_id TEXT NOT NULL,
                object_name TEXT,
                review_status TEXT NOT NULL,
                effectiveness TEXT,
                next_decision TEXT,
                review_summary TEXT,
                review_factors TEXT,
                rag_memory_candidate INTEGER DEFAULT 0,
                payload TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_weight_exec_status_v8 ON weight_execution_feedback_v8(tenant_id, org_id, execution_status, execution_gate)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_weight_exec_object_v8 ON weight_execution_feedback_v8(object_type, object_id, task_group_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_weight_review_status_v8 ON weight_execution_reviews_v8(review_status, effectiveness, next_decision)")
        conn.commit()


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _approval_rows(ctx: UserContext) -> List[Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM weight_approval_flows_v8
            WHERE tenant_id = ? AND org_id = ?
            ORDER BY updated_at DESC
            LIMIT 600
            """,
            (ctx.tenant_id, ctx.org_id),
        ).fetchall()
    return [_row_to_approval(row) for row in rows]


def _row_to_approval(row: Any) -> Dict[str, Any]:
    return {
        "approvalId": row["approval_id"],
        "tenantId": row["tenant_id"],
        "orgId": row["org_id"],
        "taskGroupId": row["task_group_id"],
        "objectType": row["object_type"],
        "objectId": row["object_id"],
        "objectName": row["object_name"],
        "groupType": row["group_type"],
        "groupName": row["group_name"],
        "approvalStatus": row["approval_status"],
        "approvalRole": row["approval_role"],
        "executionGate": row["execution_gate"],
        "priority": row["priority"],
        "finalIntensityLevel": row["final_intensity_level"],
        "decidedBy": row["decided_by"],
        "decisionNote": row["decision_note"],
        "approvalSteps": loads(row["approval_steps"]),
        "evidenceRefs": loads(row["evidence_refs"]),
        "payload": loads(row["payload"]),
        "updatedAt": row["updated_at"],
        "decidedAt": row["decided_at"],
    }


def _row_to_execution(row: Any) -> Dict[str, Any]:
    return {
        "executionId": row["execution_id"],
        "tenantId": row["tenant_id"],
        "orgId": row["org_id"],
        "approvalId": row["approval_id"],
        "taskGroupId": row["task_group_id"],
        "objectType": row["object_type"],
        "objectId": row["object_id"],
        "objectName": row["object_name"],
        "groupType": row["group_type"],
        "groupName": row["group_name"],
        "executionStatus": row["execution_status"],
        "executionGate": row["execution_gate"],
        "plannedActions": loads(row["planned_actions"]),
        "actualActions": loads(row["actual_actions"]),
        "beforeState": loads(row["before_state"]),
        "afterState": loads(row["after_state"]),
        "resultMetrics": loads(row["result_metrics"]),
        "evidenceRefs": loads(row["evidence_refs"]),
        "executorId": row["executor_id"],
        "feedbackNote": row["feedback_note"],
        "payload": loads(row["payload"]),
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
        "completedAt": row["completed_at"],
    }


def _row_to_review(row: Any) -> Dict[str, Any]:
    return {
        "reviewId": row["review_id"],
        "tenantId": row["tenant_id"],
        "orgId": row["org_id"],
        "executionId": row["execution_id"],
        "approvalId": row["approval_id"],
        "taskGroupId": row["task_group_id"],
        "objectType": row["object_type"],
        "objectId": row["object_id"],
        "objectName": row["object_name"],
        "reviewStatus": row["review_status"],
        "effectiveness": row["effectiveness"],
        "nextDecision": row["next_decision"],
        "reviewSummary": row["review_summary"],
        "reviewFactors": loads(row["review_factors"]),
        "ragMemoryCandidate": bool(row["rag_memory_candidate"]),
        "payload": loads(row["payload"]),
        "createdAt": row["created_at"],
    }


def _planned_actions(approval: Dict[str, Any]) -> List[Dict[str, Any]]:
    refs = approval.get("evidenceRefs") or {}
    conclusion = refs.get("conclusion") or approval.get("decisionNote") or "审批通过的权重任务组。"
    return [{"actionId": make_id("WACT"), "title": approval.get("groupName") or "权重动作", "scope": approval.get("groupType"), "instruction": conclusion, "status": "awaiting_feedback"}]


def _insert_execution(item: Dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO weight_execution_feedback_v8 (
                execution_id, tenant_id, org_id, approval_id, task_group_id, object_type, object_id, object_name,
                group_type, group_name, execution_status, execution_gate, planned_actions, actual_actions,
                before_state, after_state, result_metrics, evidence_refs, executor_id, feedback_note,
                payload, created_at, updated_at, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (item["executionId"], item["tenantId"], item["orgId"], item["approvalId"], item["taskGroupId"], item["objectType"], item["objectId"], item.get("objectName"), item.get("groupType"), item.get("groupName"), item["executionStatus"], item["executionGate"], dumps(item.get("plannedActions") or []), dumps(item.get("actualActions") or []), dumps(item.get("beforeState") or {}), dumps(item.get("afterState") or {}), dumps(item.get("resultMetrics") or {}), dumps(item.get("evidenceRefs") or {}), item.get("executorId"), item.get("feedbackNote"), dumps(item.get("payload") or {}), item["createdAt"], item["updatedAt"], item.get("completedAt")),
        )
        conn.commit()


def _update_task_group_status(task_group_id: str, status: str) -> None:
    with connect() as conn:
        conn.execute("UPDATE weight_task_groups_v8 SET group_status = ? WHERE task_group_id = ?", (status, task_group_id))
        conn.commit()


def generate_weight_executions(ctx: UserContext) -> Dict[str, Any]:
    ensure_weight_execution_tables()
    approvals = _approval_rows(ctx)
    if not approvals:
        generate_weight_approvals(ctx)
        approvals = _approval_rows(ctx)
    approved = [item for item in approvals if item.get("approvalStatus") == "approved" and item.get("executionGate") == "ready_for_execution"]
    created: List[Dict[str, Any]] = []
    with connect() as conn:
        existing = {row["approval_id"] for row in conn.execute("SELECT approval_id FROM weight_execution_feedback_v8 WHERE tenant_id = ? AND org_id = ?", (ctx.tenant_id, ctx.org_id)).fetchall()}
    for approval in approved:
        if approval["approvalId"] in existing:
            continue
        item = {
            "executionId": make_id("WEXEC"),
            "tenantId": approval["tenantId"],
            "orgId": approval["orgId"],
            "approvalId": approval["approvalId"],
            "taskGroupId": approval["taskGroupId"],
            "objectType": approval["objectType"],
            "objectId": approval["objectId"],
            "objectName": approval.get("objectName"),
            "groupType": approval.get("groupType"),
            "groupName": approval.get("groupName"),
            "executionStatus": "awaiting_feedback",
            "executionGate": "feedback_required",
            "plannedActions": _planned_actions(approval),
            "actualActions": [],
            "beforeState": {"approvalStatus": approval.get("approvalStatus"), "finalIntensityLevel": approval.get("finalIntensityLevel")},
            "afterState": {},
            "resultMetrics": {},
            "evidenceRefs": approval.get("evidenceRefs") or {},
            "executorId": None,
            "feedbackNote": None,
            "payload": {"version": V89_EXECUTION_VERSION, "rule": "V8.9 只记录人工执行结果，不直接调用外部平台执行。"},
            "createdAt": now_iso(),
            "updatedAt": now_iso(),
            "completedAt": None,
        }
        created.append(item)
        _insert_execution(item)
        _update_task_group_status(item["taskGroupId"], "execution_feedback_required")
    return _execution_stats(created, extra={"version": V89_EXECUTION_VERSION, "createdCount": len(created), "rule": "V8.9 生成执行回写记录，等待人工提交执行结果。"})


def _execution_stats(executions: List[Dict[str, Any]], extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    by_status: Dict[str, int] = defaultdict(int)
    by_gate: Dict[str, int] = defaultdict(int)
    by_object: Dict[str, int] = defaultdict(int)
    for item in executions:
        by_status[item["executionStatus"]] += 1
        by_gate[item["executionGate"]] += 1
        by_object[item["objectType"]] += 1
    result = {"byExecutionStatus": dict(by_status), "byExecutionGate": dict(by_gate), "byObjectType": dict(by_object), "executions": executions}
    if extra:
        result.update(extra)
    return result


def weight_execution_summary(ctx: UserContext, execution_status: str | None = None, object_type: str | None = None, limit: int = 200) -> Dict[str, Any]:
    ensure_weight_execution_tables()
    filters = ["tenant_id = ?", "org_id = ?"]
    params: List[Any] = [ctx.tenant_id, ctx.org_id]
    if execution_status:
        filters.append("execution_status = ?")
        params.append(execution_status)
    if object_type in {"product", "store", "operator"}:
        filters.append("object_type = ?")
        params.append(object_type)
    params.append(limit)
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM weight_execution_feedback_v8 WHERE {' AND '.join(filters)} ORDER BY updated_at DESC LIMIT ?", tuple(params)).fetchall()
    executions = [_row_to_execution(row) for row in rows]
    return _execution_stats(executions, extra={"version": V89_EXECUTION_VERSION, "tenantId": ctx.tenant_id, "orgId": ctx.org_id, "roleId": ctx.role_id, "executionCount": len(executions), "rule": "V8.9 展示执行回写状态，不代表系统自动执行。"})


def submit_weight_execution_feedback(execution_id: str, body: Dict[str, Any], ctx: UserContext) -> Dict[str, Any]:
    ensure_weight_execution_tables()
    with connect() as conn:
        row = conn.execute("SELECT * FROM weight_execution_feedback_v8 WHERE execution_id = ? AND tenant_id = ? AND org_id = ?", (execution_id, ctx.tenant_id, ctx.org_id)).fetchone()
    if not row:
        raise ValueError("execution not found")
    item = _row_to_execution(row)
    actual_actions = body.get("actualActions") or body.get("actual_actions") or [{"action": body.get("action") or "人工已执行权重任务组", "status": "done"}]
    after_state = body.get("afterState") or body.get("after_state") or {"manualFeedback": True}
    result_metrics = body.get("resultMetrics") or body.get("result_metrics") or {}
    evidence_refs = body.get("evidenceRefs") or body.get("evidence_refs") or item.get("evidenceRefs") or {}
    note = str(body.get("note") or body.get("feedbackNote") or "人工执行结果已回写。")
    updated = now_iso()
    with connect() as conn:
        conn.execute(
            """
            UPDATE weight_execution_feedback_v8
            SET execution_status = ?, execution_gate = ?, actual_actions = ?, after_state = ?, result_metrics = ?, evidence_refs = ?, executor_id = ?, feedback_note = ?, updated_at = ?, completed_at = ?
            WHERE execution_id = ?
            """,
            ("feedback_submitted", "review_pending", dumps(actual_actions), dumps(after_state), dumps(result_metrics), dumps(evidence_refs), ctx.user_id, note, updated, updated, execution_id),
        )
        conn.commit()
    _update_task_group_status(item["taskGroupId"], "feedback_submitted")
    item.update({"executionStatus": "feedback_submitted", "executionGate": "review_pending", "actualActions": actual_actions, "afterState": after_state, "resultMetrics": result_metrics, "evidenceRefs": evidence_refs, "executorId": ctx.user_id, "feedbackNote": note, "updatedAt": updated, "completedAt": updated})
    review = _build_review(item)
    _insert_review(review)
    return {"version": V89_EXECUTION_VERSION, "execution": item, "review": review, "rule": "执行结果已回写并生成复盘；系统仍未自动执行外部动作。"}


def _effectiveness(metrics: Dict[str, Any]) -> tuple[str, str, str]:
    roi_delta = _num(metrics.get("roiDelta"), 0.0)
    risk_delta = _num(metrics.get("riskDelta"), 0.0)
    complaint_delta = _num(metrics.get("complaintDelta"), 0.0)
    if roi_delta > 0 or risk_delta < 0 or complaint_delta < 0:
        return "effective", "keep_or_restore", "执行后核心指标改善，可保留当前权重策略并继续观察。"
    if roi_delta < -0.05 or risk_delta > 0.1 or complaint_delta > 0.1:
        return "worse", "escalate_review", "执行后指标恶化，需要升级复核或调整策略。"
    return "uncertain", "continue_observation", "执行后指标变化不明显，继续观察一个周期。"


def _build_review(execution: Dict[str, Any]) -> Dict[str, Any]:
    effectiveness, next_decision, summary = _effectiveness(execution.get("resultMetrics") or {})
    factors = {"resultMetrics": execution.get("resultMetrics") or {}, "actualActionCount": len(execution.get("actualActions") or []), "objectType": execution.get("objectType")}
    return {"reviewId": make_id("WREV"), "tenantId": execution["tenantId"], "orgId": execution["orgId"], "executionId": execution["executionId"], "approvalId": execution["approvalId"], "taskGroupId": execution["taskGroupId"], "objectType": execution["objectType"], "objectId": execution["objectId"], "objectName": execution.get("objectName"), "reviewStatus": "review_generated", "effectiveness": effectiveness, "nextDecision": next_decision, "reviewSummary": summary, "reviewFactors": factors, "ragMemoryCandidate": effectiveness in {"effective", "worse"}, "payload": {"version": V89_EXECUTION_VERSION, "rule": "复盘结果可作为后续 RAG 案例候选，但不自动改写规则。"}, "createdAt": now_iso()}


def _insert_review(item: Dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO weight_execution_reviews_v8 (
                review_id, tenant_id, org_id, execution_id, approval_id, task_group_id, object_type, object_id, object_name,
                review_status, effectiveness, next_decision, review_summary, review_factors, rag_memory_candidate, payload, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (item["reviewId"], item["tenantId"], item["orgId"], item["executionId"], item["approvalId"], item["taskGroupId"], item["objectType"], item["objectId"], item.get("objectName"), item["reviewStatus"], item["effectiveness"], item["nextDecision"], item["reviewSummary"], dumps(item.get("reviewFactors") or {}), 1 if item.get("ragMemoryCandidate") else 0, dumps(item.get("payload") or {}), item["createdAt"]),
        )
        conn.commit()


def generate_weight_execution_reviews(ctx: UserContext) -> Dict[str, Any]:
    ensure_weight_execution_tables()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM weight_execution_feedback_v8
            WHERE tenant_id = ? AND org_id = ? AND execution_status = 'feedback_submitted'
            ORDER BY updated_at DESC
            LIMIT 300
            """,
            (ctx.tenant_id, ctx.org_id),
        ).fetchall()
    created: List[Dict[str, Any]] = []
    for row in rows:
        review = _build_review(_row_to_execution(row))
        created.append(review)
        _insert_review(review)
    return _review_stats(created, extra={"version": V89_EXECUTION_VERSION, "createdCount": len(created), "rule": "V8.9 根据已回写执行结果生成复盘。"})


def _review_stats(reviews: List[Dict[str, Any]], extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    by_effectiveness: Dict[str, int] = defaultdict(int)
    by_next: Dict[str, int] = defaultdict(int)
    by_object: Dict[str, int] = defaultdict(int)
    for item in reviews:
        by_effectiveness[item["effectiveness"]] += 1
        by_next[item["nextDecision"]] += 1
        by_object[item["objectType"]] += 1
    result = {"byEffectiveness": dict(by_effectiveness), "byNextDecision": dict(by_next), "byObjectType": dict(by_object), "reviews": reviews}
    if extra:
        result.update(extra)
    return result


def weight_execution_review_summary(ctx: UserContext, effectiveness: str | None = None, object_type: str | None = None, limit: int = 200) -> Dict[str, Any]:
    ensure_weight_execution_tables()
    filters = ["tenant_id = ?", "org_id = ?"]
    params: List[Any] = [ctx.tenant_id, ctx.org_id]
    if effectiveness:
        filters.append("effectiveness = ?")
        params.append(effectiveness)
    if object_type in {"product", "store", "operator"}:
        filters.append("object_type = ?")
        params.append(object_type)
    params.append(limit)
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM weight_execution_reviews_v8 WHERE {' AND '.join(filters)} ORDER BY created_at DESC LIMIT ?", tuple(params)).fetchall()
    reviews = [_row_to_review(row) for row in rows]
    return _review_stats(reviews, extra={"version": V89_EXECUTION_VERSION, "tenantId": ctx.tenant_id, "orgId": ctx.org_id, "roleId": ctx.role_id, "reviewCount": len(reviews), "rule": "复盘案例只作为 RAG 候选，不自动改写标准线。"})
