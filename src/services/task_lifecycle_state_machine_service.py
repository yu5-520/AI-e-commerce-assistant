"""V12.9 unified task lifecycle state machine.

This service is the only write entrance for visible task lifecycle transitions.
It keeps the in-memory task pool, lifecycle projection, event log, SQLite mirror
and frontend projection on the same task_id.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Tuple

from src.services import module_task_service
from src.services.account_service import current_user
from src.services.task_lifecycle_orchestrator_service import TASK_LIFECYCLE_VERSION as ORCHESTRATOR_VERSION
from src.services.task_lifecycle_orchestrator_service import attach_lifecycle, complete_recap_and_create_rag_candidate, handle_evidence_submitted, handle_manager_reviewed
from src.services.task_state_machine_service import mirror_all

TASK_LIFECYCLE_STATE_MACHINE_VERSION = "12.9.0"
DONE_STATUS = {"已完成", "已拒绝", "已确认", "已归档", "已通过", "已写入复盘"}
WAITING_ACCEPT = {"待接收", "待确认", "已派发", "待处理", "待拆分"}
PROCESSING = {"处理中", "已退回"}
REVIEWING = {"已提交", "待复核", "待审批", "待老板确认"}

STAGE_BY_ACTION = {
    "accept": "accepted",
    "submit": "evidence_submitted",
    "review_approve": "recap_scheduled",
    "review_return": "returned",
    "complete": "recap_scheduled",
    "recap_complete": "rag_candidate_created",
}

EVENT_BY_ACTION = {
    "accept": "operator_accepted",
    "submit": "operator_submitted",
    "review_approve": "manager_approved",
    "review_return": "manager_returned",
    "complete": "task_completed",
    "recap_complete": "task_written_to_recap",
}


def now_iso() -> str:
    return datetime.now().isoformat()


def _task_id(task: Dict[str, Any] | None) -> str | None:
    return (task or {}).get("id") or (task or {}).get("taskId")


def _find_primary_task(task_id: str | None) -> Tuple[Dict[str, Any] | None, Dict[str, Any]]:
    if not task_id:
        return None, {"requestedTaskId": task_id, "resolvedBy": "missing_id"}
    exact = module_task_service.find_task(task_id)
    if exact:
        if exact.get("queueType") == "merged_duplicate" and exact.get("clusterParentTaskId"):
            parent = module_task_service.find_task(exact.get("clusterParentTaskId"))
            if parent:
                return parent, {"requestedTaskId": task_id, "resolvedTaskId": parent.get("id"), "resolvedBy": "merged_duplicate_parent"}
        return exact, {"requestedTaskId": task_id, "resolvedTaskId": exact.get("id"), "resolvedBy": "exact"}
    for task in module_task_service.TASKS:
        linked = set(task.get("clusterTaskIds") or []) | set(task.get("childTaskIds") or [])
        linked |= {str(item.get("taskId") or item.get("id") or item.get("productId")) for item in (task.get("affectedProducts") or []) if isinstance(item, dict)}
        if task_id in linked:
            return task, {"requestedTaskId": task_id, "resolvedTaskId": task.get("id"), "resolvedBy": "cluster_or_affected_child"}
    return None, {"requestedTaskId": task_id, "resolvedBy": "not_found"}


def _is_manager_required(task: Dict[str, Any]) -> bool:
    gate = task.get("actionAuthorization") or task.get("v1282ActionGate") or task.get("v127ActionGate") or {}
    decision = gate.get("decision")
    return bool(decision in {"manager_approval_required", "owner_approval_required"} or task.get("taskLayer") == "manager_approval")


def _status_patch(task: Dict[str, Any], action: str, actor_user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    note = payload.get("note") or payload.get("summary") or ""
    if action == "accept":
        return {"status": "处理中", "workflowStatus": "处理中", "displayStatus": "处理中", "acceptedById": actor_user_id, "acceptedAt": now_iso(), "lifecycleStage": "accepted", "lifecycleVersion": TASK_LIFECYCLE_STATE_MACHINE_VERSION}
    if action == "submit":
        if _is_manager_required(task):
            return {"status": "待复核", "workflowStatus": "待复核", "displayStatus": "待复核", "submissionNote": note or "运营已提交处理材料。", "submittedById": actor_user_id, "submittedAt": now_iso(), "lifecycleStage": "evidence_submitted", "lifecycleVersion": TASK_LIFECYCLE_STATE_MACHINE_VERSION}
        return {"status": "已完成", "workflowStatus": "等待自动复盘", "displayStatus": "等待自动复盘", "submissionNote": note or "运营已提交处理材料，系统进入自动复盘等待。", "submittedById": actor_user_id, "submittedAt": now_iso(), "lifecycleStage": "recap_scheduled", "lifecycleVersion": TASK_LIFECYCLE_STATE_MACHINE_VERSION}
    if action == "review_approve":
        return {"status": "已完成", "workflowStatus": "等待自动复盘", "displayStatus": "等待自动复盘", "reviewResult": "通过", "reviewNote": note or "复核通过，系统生成自动复盘周期。", "reviewerId": actor_user_id, "reviewedAt": now_iso(), "lifecycleStage": "recap_scheduled", "lifecycleVersion": TASK_LIFECYCLE_STATE_MACHINE_VERSION}
    if action == "review_return":
        return {"status": "已退回", "workflowStatus": "已退回", "displayStatus": "已退回", "reviewResult": "退回", "reviewNote": note or "复核退回，运营补充材料后再次提交。", "reviewerId": actor_user_id, "reviewedAt": now_iso(), "lifecycleStage": "returned", "lifecycleVersion": TASK_LIFECYCLE_STATE_MACHINE_VERSION}
    if action == "complete":
        return {"status": "已完成", "workflowStatus": "等待自动复盘", "displayStatus": "等待自动复盘", "completedById": actor_user_id, "completedAt": now_iso(), "lifecycleStage": "recap_scheduled", "lifecycleVersion": TASK_LIFECYCLE_STATE_MACHINE_VERSION}
    return {}


def _transition_message(action: str, task: Dict[str, Any], payload: Dict[str, Any]) -> str:
    note = payload.get("note") or ""
    return {
        "accept": note or "运营已接收任务，进入处理中。",
        "submit": note or ("运营已提交处理材料，等待总管复核。" if _is_manager_required(task) else "运营已提交处理材料，系统进入自动复盘等待。"),
        "review_approve": note or "总管复核通过，系统生成自动复盘周期。",
        "review_return": note or "总管复核退回，运营补充材料后再次提交。",
        "complete": note or "任务已完成，系统进入自动复盘等待。",
        "recap_complete": note or "系统复盘完成，生成RAG候选。",
    }.get(action, note or "任务生命周期已更新。")


def _mirror_runtime() -> Dict[str, Any]:
    try:
        return mirror_all(module_task_service.TASKS, module_task_service.TASK_EVENTS, module_task_service.LOGS)
    except Exception as exc:
        return {"ok": False, "mirrorError": str(exc)}


def _apply_orchestrator(task_id: str, action: str, actor_user_id: str, payload: Dict[str, Any]) -> Dict[str, Any] | None:
    if action == "accept":
        return attach_lifecycle(task_id, stage="accepted", event="operator_accepted", payload=payload, actor_user_id=actor_user_id)
    if action == "submit":
        task, _ = _find_primary_task(task_id)
        if task and _is_manager_required(task):
            return handle_evidence_submitted(task_id, evidence={"summary": payload.get("note") or "运营已提交处理材料。"}, actor_user_id=actor_user_id)
        return handle_manager_reviewed(task_id, approved=True, review={"comment": payload.get("note") or "运营提交后自动进入复盘周期。"}, actor_user_id=actor_user_id)
    if action == "review_approve":
        return handle_manager_reviewed(task_id, approved=True, review={"comment": payload.get("note")}, actor_user_id=actor_user_id)
    if action == "review_return":
        return handle_manager_reviewed(task_id, approved=False, review={"comment": payload.get("note")}, actor_user_id=actor_user_id)
    if action == "complete":
        return attach_lifecycle(task_id, stage="recap_scheduled", event="task_completed_recap_scheduled", payload=payload, actor_user_id=actor_user_id)
    return None


def project_lifecycle_task(task: Dict[str, Any], viewer_id: str | None = None) -> Dict[str, Any]:
    from src.services.v105_cross_account_flow_service import apply_v105_cross_account_flow, projected_task_for_role
    from src.services.v106_task_action_simplifier import apply_v106_task_actions
    from src.services.task_lifecycle_orchestrator_service import apply_lifecycle_to_task_projection

    user = current_user(viewer_id) if viewer_id else None
    role_task = projected_task_for_role(apply_v105_cross_account_flow(deepcopy(task)), (user or {}).get("roleId"))
    role_task = apply_lifecycle_to_task_projection(role_task)
    return apply_v106_task_actions(role_task)


def get_lifecycle_task_projection(task_id: str, viewer_id: str | None = None) -> Dict[str, Any] | None:
    task, _ = _find_primary_task(task_id)
    return project_lifecycle_task(task, viewer_id) if task else None


def transition_lifecycle_task(task_id: str, action: str, *, actor_user_id: str, payload: Dict[str, Any] | None = None, ctx: Any | None = None) -> Dict[str, Any]:
    payload = payload or {}
    task, resolution = _find_primary_task(task_id)
    if not task:
        return {"ok": False, "version": TASK_LIFECYCLE_STATE_MACHINE_VERSION, "action": action, "message": "任务不存在或聚合主任务未找到。", "resolution": resolution}
    if task.get("displayState") == "backend_only" or task.get("queueType") == "merged_duplicate":
        return {"ok": False, "version": TASK_LIFECYCLE_STATE_MACHINE_VERSION, "action": action, "message": "该任务为后端合并子任务，不能直接流转。", "resolution": resolution}
    primary_id = str(task.get("id"))
    before_status = task.get("status")
    before_workflow = task.get("workflowStatus")
    if action == "recap_complete":
        updated = complete_recap_and_create_rag_candidate(primary_id, before_metrics=payload.get("beforeMetrics") or {}, after_metrics=payload.get("afterMetrics") or {}, reviewer_id=actor_user_id, conclusion=payload.get("conclusion") or payload.get("note"))
    else:
        patch = _status_patch(task, action, actor_user_id, payload)
        if not patch:
            return {"ok": False, "version": TASK_LIFECYCLE_STATE_MACHINE_VERSION, "action": action, "message": f"不支持的生命周期动作：{action}", "resolution": resolution}
        message = _transition_message(action, task, payload)
        updated = module_task_service.update_task(primary_id, patch, log_type="任务生命周期", action=EVENT_BY_ACTION.get(action, action), result=message)
        if updated:
            orchestrated = _apply_orchestrator(primary_id, action, actor_user_id, payload)
            if orchestrated:
                updated = orchestrated
    latest, _ = _find_primary_task(primary_id)
    latest = latest or updated or task
    event_type = EVENT_BY_ACTION.get(action, "task_updated")
    event = module_task_service.create_task_event(latest, event_type, actor_user_id=actor_user_id, from_status=before_status, from_workflow=before_workflow, message=_transition_message(action, latest, payload))
    mirror_result = _mirror_runtime()
    projected = project_lifecycle_task(latest, actor_user_id)
    return {
        "ok": True,
        "version": TASK_LIFECYCLE_STATE_MACHINE_VERSION,
        "orchestratorVersion": ORCHESTRATOR_VERSION,
        "action": action,
        "eventType": event_type,
        "message": _transition_message(action, latest, payload),
        "resolution": resolution,
        "fromStatus": before_status,
        "toStatus": latest.get("status"),
        "fromWorkflowStatus": before_workflow,
        "toWorkflowStatus": latest.get("workflowStatus"),
        "task": projected,
        "event": event,
        "mirror": mirror_result,
        "rule": "V12.9：接收、提交、复核、复盘必须通过统一生命周期状态机写状态、事件、日志、镜像和前端投影。",
    }


def lifecycle_state_summary(limit: int = 80) -> Dict[str, Any]:
    tasks = module_task_service.list_tasks(active_only=False)[:limit]
    counts: Dict[str, int] = {}
    for task in tasks:
        stage = task.get("lifecycleStage") or (task.get("taskLifecycle") or {}).get("stage") or "generated"
        counts[stage] = counts.get(stage, 0) + 1
    return {"version": TASK_LIFECYCLE_STATE_MACHINE_VERSION, "counts": counts, "taskCount": len(tasks), "eventCount": len(module_task_service.TASK_EVENTS), "rule": "同一个task_id贯穿生成、接收、提交、复核、自动复盘和RAG候选。"}
