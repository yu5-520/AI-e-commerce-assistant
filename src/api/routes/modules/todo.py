"""Todo module routes for V12.13.1.

GET /todo is a reader. Clustering and auto-accept are explicit lifecycle sync
operations, not page-load side effects.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request

from src.core.context import UserContext, context_from_headers, get_current_context
from src.repositories.task_repository import TaskRepository
from src.services.account_service import current_user, user_has_permission, user_id_from_headers
from src.services.module_task_service import get_task_counters_for_user, list_task_events_for_user, list_tasks, pin_task, reorder_task
from src.services.task_cluster_service import TASK_CLUSTER_VERSION, cluster_open_tasks
from src.services.task_evidence_service import get_task_evidence, review_task_evidence, submit_task_evidence
from src.services.task_lifecycle_state_machine_service import TASK_LIFECYCLE_STATE_MACHINE_VERSION, auto_accept_ready_tasks, get_lifecycle_task_projection, lifecycle_state_summary, project_lifecycle_task, transition_lifecycle_task
from src.services.task_repository_write_service import reset_tasks_with_repository

router = APIRouter()
DONE_STATUS = {"已完成", "已拒绝", "已确认", "已归档", "已通过", "已写入复盘"}
TODO_VERSION = "12.13.1"


def request_user_id(request: Request) -> str:
    return user_id_from_headers(request.headers)


def require_any_permission(user_id: str, permissions: set[str]) -> None:
    if not any(user_has_permission(user_id, permission) for permission in permissions):
        user = current_user(user_id)
        raise HTTPException(status_code=403, detail=f"{user['roleName']} does not have permission for this action")


def _viewer_for_query(user_id: str | None) -> str | None:
    return None if (current_user(user_id) or {}).get("roleId") == "owner" else user_id


def _project_task(task: Dict[str, Any], user_id: str | None) -> Dict[str, Any]:
    return project_lifecycle_task(task, user_id)


def _project_tasks(tasks: List[Dict[str, Any]], user_id: str | None) -> List[Dict[str, Any]]:
    return [_project_task(task, user_id) for task in tasks if task.get("displayState") != "backend_only" and task.get("queueType") != "merged_duplicate"]


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
        "waitingRecap": len([task for task in visible if task.get("workflowStatus") == "等待自动复盘" or task.get("lifecycleStage") == "recap_scheduled"]),
        "recentEvents": len(events or []),
        "latestEvent": (events or [None])[0],
    }


def _load_tasks(ctx: UserContext, *, viewer_id: str | None, assignee_id: str | None, review_scope: bool) -> tuple[list[Dict[str, Any]], list[Dict[str, Any]], str]:
    tasks = list_tasks(assignee_id=assignee_id, review_scope=review_scope, viewer_id=viewer_id)
    active_tasks = list_tasks(active_only=True, assignee_id=assignee_id, review_scope=review_scope, viewer_id=viewer_id)
    if tasks or active_tasks:
        return tasks, active_tasks, "memory"
    return _repository_fallback(ctx, active_only=False, assignee_id=assignee_id), _repository_fallback(ctx, active_only=True, assignee_id=assignee_id), "repository"


def _transition_or_404(task_id: str, action: str, *, viewer_id: str, payload: Dict[str, Any] | None = None, ctx: UserContext | None = None) -> Dict[str, Any]:
    result = transition_lifecycle_task(task_id, action, actor_user_id=viewer_id, payload=payload or {}, ctx=ctx)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("message") or "task transition failed")
    return result


@router.get("/todo")
def todo(request: Request, scope: str = Query(default="all"), assignee_id: str | None = Query(default=None)) -> Dict[str, Any]:
    ctx = context_from_headers(request.headers)
    viewer_id = ctx.user_id
    query_viewer_id = _viewer_for_query(viewer_id)
    review_scope = scope == "review"
    mine_assignee = assignee_id if scope in {"mine", "operator"} else None
    tasks, active_tasks, source = _load_tasks(ctx, viewer_id=query_viewer_id, assignee_id=mine_assignee, review_scope=review_scope)
    events = list_task_events_for_user(query_viewer_id)
    counters = _counter_from_tasks(active_tasks, events)
    return {
        "version": TODO_VERSION,
        "tasks": _project_tasks(tasks, viewer_id),
        "activeTasks": _project_tasks(active_tasks, viewer_id),
        "events": events,
        "counters": counters,
        "taskClusterSync": {"version": TASK_CLUSTER_VERSION, "skipped": True, "reason": "GET /todo is read-only in V12.13.1"},
        "autoAcceptSync": {"version": TODO_VERSION, "skipped": True, "reason": "Use POST /todo/lifecycle/sync"},
        "taskLifecycleSync": lifecycle_state_summary(limit=100),
        "scope": scope,
        "viewer": current_user(viewer_id),
        "source": source,
        "repositoryFallback": {"version": TODO_VERSION, "used": "repository" in source, "rule": "V12.13.1任务页读取不触发状态变更。"},
        "taskActionSurface": {"version": TODO_VERSION, "taskClusterVersion": TASK_CLUSTER_VERSION, "lifecycleStateMachineVersion": TASK_LIFECYCLE_STATE_MACHINE_VERSION, "rule": "生命周期同步拆到显式接口，页面GET只读。"},
        "readMode": "readonly_no_lifecycle_side_effects",
        "rule": "V12.13.1：任务页GET只读；聚合、自动接收等生命周期动作必须显式调用 /todo/lifecycle/sync。",
    }


@router.post("/todo/lifecycle/sync")
def todo_lifecycle_sync(request: Request, ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    query_viewer_id = _viewer_for_query(viewer_id)
    cluster_sync = cluster_open_tasks()
    tasks, active_tasks, source = _load_tasks(ctx, viewer_id=query_viewer_id, assignee_id=None, review_scope=False)
    auto_accept_sync = auto_accept_ready_tasks(active_tasks, viewer_id=viewer_id, ctx=ctx)
    if auto_accept_sync.get("autoAcceptedCount"):
        tasks, active_tasks, second_source = _load_tasks(ctx, viewer_id=query_viewer_id, assignee_id=None, review_scope=False)
        source = f"{source}+auto_accept->{second_source}"
    events = list_task_events_for_user(query_viewer_id)
    return {
        "version": TODO_VERSION,
        "ok": True,
        "source": source,
        "taskClusterSync": cluster_sync,
        "autoAcceptSync": auto_accept_sync,
        "tasks": _project_tasks(tasks, viewer_id),
        "activeTasks": _project_tasks(active_tasks, viewer_id),
        "events": events,
        "counters": _counter_from_tasks(active_tasks, events),
        "taskLifecycleSync": lifecycle_state_summary(limit=100),
        "rule": "V12.13.1：生命周期动作显式同步，不再挂在页面GET。",
    }


@router.get("/todo/lifecycle/summary")
def todo_lifecycle_summary() -> Dict[str, Any]:
    return lifecycle_state_summary(limit=100)


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


@router.post("/todo/{task_id}/accept")
def accept_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"submit_tasks", "handle_tasks", "assign_tasks", "dispatch_tasks"})
    return _transition_or_404(task_id, "accept", viewer_id=viewer_id, payload=body or {"note": "运营已接收任务"}, ctx=ctx)


@router.post("/todo/{task_id}/submit")
def submit_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"submit_tasks", "handle_tasks", "dispatch_tasks", "assign_tasks"})
    return _transition_or_404(task_id, "submit", viewer_id=viewer_id, payload=body or {"note": "运营已提交处理材料。"}, ctx=ctx)


@router.post("/todo/{task_id}/review")
def review_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"review_tasks"})
    body = body or {}
    decision = body.get("decision") or "approve"
    action = "review_approve" if decision in {"approve", "approved", "pass", "通过"} else "review_return"
    return _transition_or_404(task_id, action, viewer_id=viewer_id, payload=body, ctx=ctx)


@router.post("/todo/{task_id}/submit-evidence")
def submit_evidence_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"submit_tasks", "handle_tasks", "assign_tasks", "dispatch_tasks"})
    task = submit_task_evidence(task_id, body or {}, submitter_id=viewer_id)
    if not task:
        raise HTTPException(status_code=400, detail="cannot submit task evidence")
    return _transition_or_404(task_id, "submit", viewer_id=viewer_id, payload=body or {"note": "运营已提交处理材料。"}, ctx=ctx)


@router.post("/todo/{task_id}/review-evidence")
def review_evidence_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"review_tasks"})
    task = review_task_evidence(task_id, body or {}, reviewer_id=viewer_id)
    if not task:
        raise HTTPException(status_code=400, detail="cannot review task evidence")
    decision = (body or {}).get("decision") or "approve"
    action = "review_approve" if decision in {"approve", "approved", "pass", "通过"} else "review_return"
    return _transition_or_404(task_id, action, viewer_id=viewer_id, payload=body or {}, ctx=ctx)


@router.post("/todo/{task_id}/recap/complete")
def complete_recap_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"review_tasks", "assign_tasks", "dispatch_tasks"})
    return _transition_or_404(task_id, "recap_complete", viewer_id=viewer_id, payload=body or {}, ctx=ctx)


@router.post("/todo/{task_id}/recap")
def recap_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return complete_recap_todo(request, task_id, body, ctx)


@router.post("/todo/{task_id}/complete")
def complete_todo(request: Request, task_id: str, ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"review_tasks", "submit_tasks", "dispatch_tasks", "assign_tasks"})
    return _transition_or_404(task_id, "complete", viewer_id=viewer_id, payload={}, ctx=ctx)


@router.post("/todo/{task_id}/split")
def split_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"assign_tasks", "dispatch_tasks"})
    return _transition_or_404(task_id, "split", viewer_id=viewer_id, payload=body or {}, ctx=ctx)


@router.post("/todo/{task_id}/assign")
def assign_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"assign_tasks", "dispatch_tasks"})
    return _transition_or_404(task_id, "assign", viewer_id=viewer_id, payload=body or {}, ctx=ctx)


@router.post("/todo/{task_id}/pin")
def pin_todo(request: Request, task_id: str) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"assign_tasks", "dispatch_tasks"})
    task = pin_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return {"ok": True, "version": TODO_VERSION, "task": get_lifecycle_task_projection(task_id, viewer_id) or _project_task(task, viewer_id)}


@router.post("/todo/{task_id}/reorder")
def reorder_todo(request: Request, task_id: str, direction: str = Query(default="down")) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"assign_tasks", "dispatch_tasks"})
    task = reorder_task(task_id, direction=direction)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return {"ok": True, "version": TODO_VERSION, "task": get_lifecycle_task_projection(task_id, viewer_id) or _project_task(task, viewer_id)}


@router.post("/todo/reset")
def reset_todo(request: Request, ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"assign_tasks", "dispatch_tasks"})
    return reset_tasks_with_repository(ctx, reason="todo reset")
