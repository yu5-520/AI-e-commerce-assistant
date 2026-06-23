"""V8.8 weight approval flow service.

V8.7 creates cross-generated weight task-group drafts. V8.8 adds an approval
flow and execution gate on top of those drafts. Approval can unlock a task group
for the later execution layer, but this version still does not execute any
weight action, change permissions, remove products, or adjust spend.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from src.core.context import UserContext
from src.repositories.sqlite_repository import connect, dumps, loads
from src.services.v87_weight_task_group_service import ensure_weight_task_group_tables, generate_weight_task_groups

V88_APPROVAL_VERSION = "8.8.0"

ROLE_LEVEL = {"operator": 1, "finance": 2, "manager": 3, "owner": 4}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}".upper()


def ensure_weight_approval_tables() -> None:
    ensure_weight_task_group_tables()
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS weight_approval_flows_v8 (
                approval_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                org_id TEXT NOT NULL,
                task_group_id TEXT NOT NULL,
                object_type TEXT NOT NULL,
                object_id TEXT NOT NULL,
                object_name TEXT,
                group_type TEXT,
                group_name TEXT,
                approval_status TEXT NOT NULL,
                approval_role TEXT,
                approval_required INTEGER DEFAULT 1,
                execution_gate TEXT NOT NULL,
                priority TEXT,
                final_intensity_level TEXT,
                requested_by TEXT,
                decided_by TEXT,
                decision_note TEXT,
                approval_steps TEXT,
                evidence_refs TEXT,
                payload TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                decided_at TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_weight_approvals_group_v8 ON weight_approval_flows_v8(tenant_id, org_id, task_group_id, approval_status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_weight_approvals_status_v8 ON weight_approval_flows_v8(approval_status, execution_gate, approval_role)")
        conn.commit()


def _role_can(ctx: UserContext, required_role: str | None) -> bool:
    required = required_role or "manager"
    return ROLE_LEVEL.get(ctx.role_id, 0) >= ROLE_LEVEL.get(required, 3)


def _row_to_group(row: Any) -> Dict[str, Any]:
    return {
        "taskGroupId": row["task_group_id"],
        "tenantId": row["tenant_id"],
        "orgId": row["org_id"],
        "objectType": row["object_type"],
        "objectId": row["object_id"],
        "objectName": row["object_name"],
        "groupType": row["group_type"],
        "groupName": row["group_name"],
        "groupStatus": row["group_status"],
        "priority": row["priority"],
        "approvalRequired": bool(row["approval_required"]),
        "approvalRole": row["approval_role"],
        "finalIntensityLevel": row["final_intensity_level"],
        "readiness": row["readiness"],
        "validationStatus": row["validation_status"],
        "taskCount": row["task_count"],
        "tasks": loads(row["tasks"]),
        "evidenceRefs": loads(row["evidence_refs"]),
        "payload": loads(row["payload"]),
        "createdAt": row["created_at"],
    }


def _load_task_groups(ctx: UserContext) -> List[Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM weight_task_groups_v8
            WHERE tenant_id = ? AND org_id = ?
            ORDER BY created_at DESC
            LIMIT 600
            """,
            (ctx.tenant_id, ctx.org_id),
        ).fetchall()
    seen: set[str] = set()
    groups: List[Dict[str, Any]] = []
    for row in rows:
        if row["task_group_id"] in seen:
            continue
        seen.add(row["task_group_id"])
        groups.append(_row_to_group(row))
    return groups


def _initial_status(group: Dict[str, Any]) -> tuple[str, str]:
    if group.get("groupStatus") == "pending_approval":
        return "pending", "locked"
    if group.get("groupStatus") == "evidence_review":
        return "evidence_review", "blocked"
    if group.get("groupStatus") == "human_review_draft":
        return "human_review", "human_review_only"
    return "draft", "blocked"


def _approval_steps(group: Dict[str, Any]) -> List[Dict[str, Any]]:
    role = group.get("approvalRole") or "manager"
    steps = [{"step": 1, "role": role, "status": "pending", "label": "权重任务组审批"}]
    if role == "owner":
        steps.insert(0, {"step": 0, "role": "manager", "status": "review", "label": "总管预审"})
    if group.get("objectType") == "operator":
        steps.append({"step": 2, "role": "owner", "status": "confirm", "label": "人员相关结论老板确认"})
    return steps


def _build_approval(group: Dict[str, Any], ctx: UserContext) -> Dict[str, Any]:
    status, gate = _initial_status(group)
    return {
        "approvalId": make_id("WAPP"),
        "tenantId": group["tenantId"],
        "orgId": group["orgId"],
        "taskGroupId": group["taskGroupId"],
        "objectType": group["objectType"],
        "objectId": group["objectId"],
        "objectName": group.get("objectName"),
        "groupType": group.get("groupType"),
        "groupName": group.get("groupName"),
        "approvalStatus": status,
        "approvalRole": group.get("approvalRole") or "manager",
        "approvalRequired": True,
        "executionGate": gate,
        "priority": group.get("priority"),
        "finalIntensityLevel": group.get("finalIntensityLevel"),
        "requestedBy": ctx.user_id,
        "decidedBy": None,
        "decisionNote": None,
        "approvalSteps": _approval_steps(group),
        "evidenceRefs": group.get("evidenceRefs") or {},
        "payload": {"version": V88_APPROVAL_VERSION, "sourceGroupStatus": group.get("groupStatus"), "rule": "V8.8 只审批任务组草案；审批通过后仍不自动执行。"},
        "createdAt": now_iso(),
        "updatedAt": now_iso(),
        "decidedAt": None,
    }


def _insert_approval(item: Dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO weight_approval_flows_v8 (
                approval_id, tenant_id, org_id, task_group_id, object_type, object_id, object_name,
                group_type, group_name, approval_status, approval_role, approval_required, execution_gate,
                priority, final_intensity_level, requested_by, decided_by, decision_note, approval_steps,
                evidence_refs, payload, created_at, updated_at, decided_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (item["approvalId"], item["tenantId"], item["orgId"], item["taskGroupId"], item["objectType"], item["objectId"], item.get("objectName"), item.get("groupType"), item.get("groupName"), item["approvalStatus"], item.get("approvalRole"), 1 if item.get("approvalRequired") else 0, item["executionGate"], item.get("priority"), item.get("finalIntensityLevel"), item.get("requestedBy"), item.get("decidedBy"), item.get("decisionNote"), dumps(item.get("approvalSteps") or []), dumps(item.get("evidenceRefs") or {}), dumps(item.get("payload") or {}), item["createdAt"], item["updatedAt"], item.get("decidedAt")),
        )
        conn.commit()


def _update_group_status(task_group_id: str, status: str) -> None:
    with connect() as conn:
        conn.execute("UPDATE weight_task_groups_v8 SET group_status = ? WHERE task_group_id = ?", (status, task_group_id))
        conn.commit()


def generate_weight_approvals(ctx: UserContext) -> Dict[str, Any]:
    ensure_weight_approval_tables()
    groups = _load_task_groups(ctx)
    if not groups:
        generate_weight_task_groups(ctx)
        groups = _load_task_groups(ctx)
    created: List[Dict[str, Any]] = []
    for group in groups:
        item = _build_approval(group, ctx)
        created.append(item)
        _insert_approval(item)
    return _approval_stats(created, extra={"version": V88_APPROVAL_VERSION, "createdCount": len(created), "rule": "V8.8 生成审批流，不执行任务组动作。"})


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
        "approvalRequired": bool(row["approval_required"]),
        "executionGate": row["execution_gate"],
        "priority": row["priority"],
        "finalIntensityLevel": row["final_intensity_level"],
        "requestedBy": row["requested_by"],
        "decidedBy": row["decided_by"],
        "decisionNote": row["decision_note"],
        "approvalSteps": loads(row["approval_steps"]),
        "evidenceRefs": loads(row["evidence_refs"]),
        "payload": loads(row["payload"]),
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
        "decidedAt": row["decided_at"],
    }


def _approval_stats(approvals: List[Dict[str, Any]], extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    by_status: Dict[str, int] = defaultdict(int)
    by_gate: Dict[str, int] = defaultdict(int)
    by_role: Dict[str, int] = defaultdict(int)
    by_object: Dict[str, int] = defaultdict(int)
    for item in approvals:
        by_status[item["approvalStatus"]] += 1
        by_gate[item["executionGate"]] += 1
        by_role[item.get("approvalRole") or "manager"] += 1
        by_object[item["objectType"]] += 1
    result = {"byApprovalStatus": dict(by_status), "byExecutionGate": dict(by_gate), "byApprovalRole": dict(by_role), "byObjectType": dict(by_object), "approvals": approvals}
    if extra:
        result.update(extra)
    return result


def weight_approval_summary(ctx: UserContext, approval_status: str | None = None, object_type: str | None = None, limit: int = 200) -> Dict[str, Any]:
    ensure_weight_approval_tables()
    filters = ["tenant_id = ?", "org_id = ?"]
    params: List[Any] = [ctx.tenant_id, ctx.org_id]
    if approval_status:
        filters.append("approval_status = ?")
        params.append(approval_status)
    if object_type in {"product", "store", "operator"}:
        filters.append("object_type = ?")
        params.append(object_type)
    params.append(limit)
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM weight_approval_flows_v8 WHERE {' AND '.join(filters)} ORDER BY created_at DESC LIMIT ?", tuple(params)).fetchall()
    approvals = [_row_to_approval(row) for row in rows]
    return _approval_stats(approvals, extra={"version": V88_APPROVAL_VERSION, "tenantId": ctx.tenant_id, "orgId": ctx.org_id, "roleId": ctx.role_id, "approvalCount": len(approvals), "rule": "V8.8 审批只打开执行门，不自动执行动作。"})


def decide_weight_approval(approval_id: str, body: Dict[str, Any], ctx: UserContext) -> Dict[str, Any]:
    ensure_weight_approval_tables()
    decision = str(body.get("decision") or body.get("action") or "").strip().lower()
    note = str(body.get("note") or body.get("decisionNote") or "").strip()
    if decision not in {"approve", "reject", "return_review"}:
        raise ValueError("decision must be approve, reject, or return_review")
    with connect() as conn:
        row = conn.execute("SELECT * FROM weight_approval_flows_v8 WHERE approval_id = ? AND tenant_id = ? AND org_id = ?", (approval_id, ctx.tenant_id, ctx.org_id)).fetchone()
    if not row:
        raise ValueError("approval not found")
    item = _row_to_approval(row)
    if not _role_can(ctx, item.get("approvalRole")):
        raise PermissionError("current role cannot decide this approval")
    if item["approvalStatus"] not in {"pending", "evidence_review", "human_review"}:
        raise ValueError("approval is already decided or closed")
    if decision == "approve":
        status = "approved" if item["objectType"] != "operator" else "reviewed"
        gate = "ready_for_execution" if item["objectType"] != "operator" else "human_review_only"
        group_status = "approved_pending_execution" if item["objectType"] != "operator" else "human_reviewed"
    elif decision == "reject":
        status = "rejected"
        gate = "blocked"
        group_status = "rejected"
    else:
        status = "returned_for_evidence"
        gate = "blocked"
        group_status = "evidence_review"
    updated = now_iso()
    with connect() as conn:
        conn.execute(
            """
            UPDATE weight_approval_flows_v8
            SET approval_status = ?, execution_gate = ?, decided_by = ?, decision_note = ?, updated_at = ?, decided_at = ?
            WHERE approval_id = ?
            """,
            (status, gate, ctx.user_id, note, updated, updated, approval_id),
        )
        conn.commit()
    _update_group_status(item["taskGroupId"], group_status)
    item.update({"approvalStatus": status, "executionGate": gate, "decidedBy": ctx.user_id, "decisionNote": note, "updatedAt": updated, "decidedAt": updated})
    return {"version": V88_APPROVAL_VERSION, "approval": item, "rule": "审批通过只进入后续执行层准备态，V8.8 不自动执行。"}
