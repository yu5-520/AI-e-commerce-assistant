"""Todo module routes.

V12.7.2 aligns the visible task queue, accept/submit/review actions and detail
reports around the same backend task id. Memory tasks are updated first, and the
repository write is best-effort sync for the demo runtime.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request

from src.core.context import UserContext, context_from_headers, get_current_context
from src.repositories.task_repository import TaskRepository
from src.services.account_service import current_user, user_has_permission, user_id_from_headers
from src.services.experience_memory_service import draft_experience_from_task
from src.services.module_task_service import get_task_counters_for_user, list_task_events_for_user, list_tasks, pin_task, reorder_task, update_task
from src.services.task_cluster_service import TASK_CLUSTER_VERSION, cluster_open_tasks
from src.services.task_evidence_service import get_task_evidence, review_task_evidence, submit_task_evidence
from src.services.task_repository_write_service import reset_tasks_with_repository, transition_task_with_repository
from src.services.v105_cross_account_flow_service import apply_v105_cross_account_flow, projected_task_for_role
from src.services.v106_task_action_simplifier import apply_v106_task_actions

router = APIRouter()
DONE_STATUS = {"已完成", "已拒绝", "已确认", "已归档", "已通过", "已写入复盘"}
TODO_VERSION = "12.7.2"


def request_user_id(request: Request) -> str:
    return user_id_from_headers(request.headers)


def require_any_permission(user_id: str, permissions: set[str]) -> None:
    if not any(user_has_permission(user_id, permission) for permission in permissions):
        user = current_user(user_id)
        raise HTTPException(status_code=403, detail=f"{user['roleName']} does not have permission for this action")


def _viewer_role(user_id: str | None) -> str | None:
    return (current_user(user_id) or {}).get("roleId") if user_id else None


def _viewer_for_query(user_id: str | None) -> str | None:
    return None if _viewer_role(user_id) == "owner" else user_id


def _v10_task(task: Dict[str, Any], user_id: str | None) -> Dict[str, Any]:
    role_task = projected_task_for_role(apply_v105_cross_account_flow(task), _viewer_role(user_id))
    return apply_v106_task_actions(role_task)


def _v10_tasks(tasks: List[Dict[str, Any]], user_id: str | None) -> List[Dict[str, Any]]:
    return [_v10_task(task, user_id) for task in tasks if task.get("displayState") != "backend_only" and task.get("queueType") != "merged_duplicate"]


def _repository_fallback(ctx: UserContext, *, active_only: bool = False, assignee_id: str | None = None) -> List[Dict[str, Any]]:
    tasks = TaskRepository(ctx).list(active_only=active_only, assignee_id=assignee_id, limit=500)
    return [task for task in tasks if not active_only or task.get("status") not in DONE_STATUS]


def _counter_from_tasks(active_tasks: List[Dict[str, Any]], events: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    visible = [task for task in active_tasks if task.get("displayState") != "backend_only" and task.get("queueType") != "merged_duplicate"]
    return {
        "visibleActive": len(visible),
        "waitingAccept": len([task for task in visible if task.get("status") in {"待接收", "待确认"}]),
        "processing": len([task for task in visible if task.get("status") == "处理中"]),
        "submitted": len([task for task in visible if task.get("status") in {"已提交", "待复核"}]),
        "reviewing": len([task for task in visible if task.get("status") == "待复核"]),
        "returned": len([task for task in visible if task.get("workflowStatus") == "已退回"]),
        "waitingRecap": len([task for task in visible if task.get("status") == "已完成" and task.get("recapTarget") in {"日报", "周报", "月报"}]),
        "recentEvents": len(events or []),
        "latestEvent": (events or [None])[0],
    }


def _safe_repo_transition(task_id: str, action: str, payload: Dict[str, Any], ctx: UserContext) -> Dict[str, Any]:
    try:
        return transition_task_with_repository(task_id, action, payload, ctx)
    except Exception as exc:
        return {"ok": False, "repositoryError": str(exc), "action": action}


def _memory_or_repo_transition(task_id: str, patch: Dict[str, Any], *, event_action: str, repo_payload: Dict[str, Any], ctx: UserContext, viewer_id: str, log_type: str, result_message: str) -> Dict[str, Any]:
    memory_task = update_task(task_id, patch, log_type=log_type, action=log_type, result=result_message)
    repo_result = _safe_repo_transition(task_id, event_action, repo_payload, ctx)
    if memory_task:
        memory_task["repositoryWrite"] = {"bestEffort": True, "result": {key: value for key, value in repo_result.items() if key != "task"}}
        return _v10_task(memory_task, viewer_id)
    task = repo_result.get("task")
    if not task:
        raise HTTPException(status_code=404, detail=repo_result.get("message") or repo_result.get("repositoryError") or "task not found")
    return _v10_task(task, viewer_id)


@router.get("/todo")
def todo(request: Request, scope: str = Query(default="all"), assignee_id: str | None = Query(default=None)) -> Dict[str, Any]:
    ctx = context_from_headers(request.headers)
    viewer_id = ctx.user_id
    query_viewer_id = _viewer_for_query(viewer_id)
    review_scope = scope == "review"
    mine_assignee = assignee_id if scope in {"mine", "operator"} else None
    cluster_sync = cluster_open_tasks()
    tasks = list_tasks(assignee_id=mine_assignee, review_scope=review_scope, viewer_id=query_viewer_id)
    active_tasks = list_tasks(active_only=True, assignee_id=mine_assignee, review_scope=review_scope, viewer_id=query_viewer_id)
    events = list_task_events_for_user(query_viewer_id)
    counters = _counter_from_tasks(active_tasks, events)
    source = "memory"
    if not tasks and not active_tasks:
        tasks = _repository_fallback(ctx, active_only=False, assignee_id=mine_assignee)
        active_tasks = _repository_fallback(ctx, active_only=True, assignee_id=mine_assignee)
        counters = _counter_from_tasks(active_tasks, events=[])
        events = []
        source = "repository"
    return {
        "version": TODO_VERSION,
        "tasks": _v10_tasks(tasks, viewer_id),
        "activeTasks": _v10_tasks(active_tasks, viewer_id),
        "events": events,
        "counters": counters,
        "taskClusterSync": cluster_sync,
        "scope": scope,
        "viewer": current_user(viewer_id),
        "source": source,
        "repositoryFallback": {"version": TODO_VERSION, "used": source == "repository", "rule": "内存任务池为空时才读Repository；正常任务生命周期以内存任务池为主，同步写Repository。"},
        "taskActionSurface": {"version": TODO_VERSION, "taskClusterVersion": TASK_CLUSTER_VERSION, "rule": "同店铺同动作同原因的任务是真实后端聚合任务，不再只是前端临时展示。"},
        "rule": "任务生成、聚合、接收、详情使用同一个后端任务ID。",
    }


@router.get("/todo/events")
def todo_events(request: Request) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    query_viewer_id = _viewer_for_query(viewer_id)
    return {"version": TODO_VERSION, "events": list_task_events_for_user(query_viewer_id), "counters": get_task_counters_for_user(query_viewer_id), "viewer": current_user(viewer_id)}


@router.get("/todo/counters")
def todo_counters(request: Request) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    query_viewer_id = _viewer_for_query(viewer_id)
    return {"version": TODO_VERSION, "counters": get_task_counters_for_user(query_viewer_id), "viewer": current_user(viewer_id)}


@router.get("/todo/{task_id}/evidence")
def todo_evidence(request: Request, task_id: str) -> Dict[str, Any]:
    evidence = get_task_evidence(task_id, viewer_id=request_user_id(request))
    if not evidence:
        raise HTTPException(status_code=404, detail="task evidence not found")
    evidence["taskActionVersion"] = TODO_VERSION
    return evidence


@router.post("/todo/{task_id}/split")
def split_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"assign_tasks", "dispatch_tasks"})
    body = body or {}
    payload = {"assigneeId": body.get("operator_id") or body.get("operatorId") or body.get("assignee_id") or body.get("assigneeId"), "reviewerId": body.get("reviewer_id") or body.get("reviewerId"), "note": body.get("note") or "", "actorUserId": viewer_id}
    return _memory_or_repo_transition(task_id, {"status": "待接收", "workflowStatus": "已派发", "assigneeId": payload.get("assigneeId"), "reviewerId": payload.get("reviewerId")}, event_action="manager_assigned", repo_payload=payload, ctx=ctx, viewer_id=viewer_id, log_type="任务派发", result_message="任务已派发。")


@router.post("/todo/{task_id}/assign")
def assign_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return split_todo(request, task_id, body, ctx)


@router.post("/todo/{task_id}/accept")
def accept_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"submit_tasks", "handle_tasks", "assign_tasks", "dispatch_tasks"})
    body = body or {}
    return _memory_or_repo_transition(task_id, {"status": "处理中", "workflowStatus": "处理中", "acceptedById": viewer_id}, event_action="operator_accepted", repo_payload={"note": body.get("note") or "运营已接收任务", "actorUserId": viewer_id}, ctx=ctx, viewer_id=viewer_id, log_type="任务接收", result_message="任务已接收，进入处理中。")


@router.post("/todo/{task_id}/submit")
def submit_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"submit_tasks", "dispatch_tasks", "assign_tasks"})
    body = body or {}
    note = body.get("note") or "运营已提交处理结果。"
    return _memory_or_repo_transition(task_id, {"status": "待复核", "workflowStatus": "待复核", "submissionNote": note, "submittedById": viewer_id}, event_action="operator_submitted", repo_payload={"note": note, "actorUserId": body.get("submitter_id") or body.get("submitterId") or viewer_id}, ctx=ctx, viewer_id=viewer_id, log_type="任务提交", result_message=note)


@router.post("/todo/{task_id}/submit-evidence")
def submit_evidence_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"submit_tasks", "handle_tasks", "assign_tasks", "dispatch_tasks"})
    task = submit_task_evidence(task_id, body or {}, submitter_id=viewer_id)
    if not task:
        raise HTTPException(status_code=400, detail="cannot submit task evidence")
    return _v10_task(task, viewer_id)


@router.post("/todo/{task_id}/review")
def review_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"review_tasks"})
    body = body or {}
    decision = body.get("decision") or "approve"
    note = body.get("note") or ("复核通过。" if decision in {"approve", "approved", "pass", "通过"} else "复核退回。")
    approved = decision in {"approve", "approved", "pass", "通过"}
    event_action = "manager_approved" if approved else "manager_returned"
    status_patch = {"status": "已完成" if approved else "已退回", "workflowStatus": "已通过" if approved else "已退回", "reviewNote": note, "reviewerId": viewer_id}
    task = _memory_or_repo_transition(task_id, status_patch, event_action=event_action, repo_payload={"note": note, "actorUserId": body.get("reviewer_id") or body.get("reviewerId") or viewer_id}, ctx=ctx, viewer_id=viewer_id, log_type="任务复核", result_message=note)
    if approved:
        task["feedbackDraft"] = draft_experience_from_task(task_id, operator_submission=task.get("submissionNote") or "运营提交内容待补充。", manager_review=task.get("reviewNote") or note, before_metrics=body.get("beforeMetrics") or body.get("before_metrics") or task.get("beforeMetrics") or {}, after_metrics=body.get("afterMetrics") or body.get("after_metrics") or task.get("afterMetrics") or {}, user_id=viewer_id)
    return task


@router.post("/todo/{task_id}/review-evidence")
def review_evidence_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"review_tasks"})
    task = review_task_evidence(task_id, body or {}, reviewer_id=viewer_id)
    if not task:
        raise HTTPException(status_code=400, detail="cannot review task evidence")
    return _v10_task(task, viewer_id)


@router.post("/todo/{task_id}/recap")
def recap_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"review_tasks", "assign_tasks", "dispatch_tasks"})
    body = body or {}
    target = body.get("recap_target") or body.get("recapTarget") or "日报"
    return _memory_or_repo_transition(task_id, {"status": "已写入复盘", "workflowStatus": "已写入复盘", "recapTarget": target}, event_action="task_written_to_recap", repo_payload={"recapTarget": target, "note": body.get("note") or "", "actorUserId": viewer_id}, ctx=ctx, viewer_id=viewer_id, log_type="写入复盘", result_message="任务已写入复盘。")


@router.post("/todo/{task_id}/complete")
def complete_todo(request: Request, task_id: str, ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"review_tasks", "submit_tasks", "dispatch_tasks", "assign_tasks"})
    return _memory_or_repo_transition(task_id, {"status": "已完成", "workflowStatus": "已完成"}, event_action="task_completed", repo_payload={"actorUserId": viewer_id}, ctx=ctx, viewer_id=viewer_id, log_type="任务完成", result_message="任务已完成。")


@router.post("/todo/{task_id}/pin")
def pin_todo(request: Request, task_id: str) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"assign_tasks", "dispatch_tasks"})
    task = pin_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return _v10_task(task, viewer_id)


@router.post("/todo/{task_id}/reorder")
def reorder_todo(request: Request, task_id: str, direction: str = "down") -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"assign_tasks", "dispatch_tasks"})
    task = reorder_task(task_id, direction)
    if not task:
        raise HTTPException(status_code=400, detail="cannot reorder task")
    return _v10_task(task, viewer_id)


@router.post("/todo/reset")
def reset_todo(request: Request, ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return reset_tasks_with_repository(ctx, reason="todo reset")
