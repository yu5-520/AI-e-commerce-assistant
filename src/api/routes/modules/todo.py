"""Todo module routes."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request

from src.core.context import UserContext, get_current_context
from src.services.account_service import current_user, user_has_permission, user_id_from_headers
from src.services.experience_memory_service import draft_experience_from_task
from src.services.module_task_service import get_task_counters_for_user, list_task_events_for_user, list_tasks, pin_task, reorder_task
from src.services.task_evidence_service import get_task_evidence, review_task_evidence, submit_task_evidence
from src.services.task_repository_write_service import reset_tasks_with_repository, transition_task_with_repository
from src.services.v105_cross_account_flow_service import apply_v105_cross_account_flow, projected_task_for_role
from src.services.v106_task_action_simplifier import apply_v106_task_actions

router = APIRouter()


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
    return [_v10_task(task, user_id) for task in tasks]


def _task_from_write_result(result: Dict[str, Any], *, error_detail: str, viewer_id: str | None = None) -> Dict[str, Any]:
    task = result.get("task")
    if not task:
        raise HTTPException(status_code=400, detail=result.get("message") or error_detail)
    task["repositoryWrite"] = {"version": result.get("version"), "action": result.get("action"), "repository": result.get("repository")}
    return _v10_task(task, viewer_id)


@router.get("/todo")
def todo(request: Request, scope: str = Query(default="all"), assignee_id: str | None = Query(default=None)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    query_viewer_id = _viewer_for_query(viewer_id)
    review_scope = scope == "review"
    mine_assignee = assignee_id if scope in {"mine", "operator"} else None
    tasks = list_tasks(assignee_id=mine_assignee, review_scope=review_scope, viewer_id=query_viewer_id)
    active_tasks = list_tasks(active_only=True, assignee_id=mine_assignee, review_scope=review_scope, viewer_id=query_viewer_id)
    return {
        "version": "10.9.0",
        "tasks": _v10_tasks(tasks, viewer_id),
        "activeTasks": _v10_tasks(active_tasks, viewer_id),
        "events": list_task_events_for_user(query_viewer_id),
        "counters": get_task_counters_for_user(query_viewer_id),
        "scope": scope,
        "viewer": current_user(viewer_id),
        "crossAccountFlow": {"version": "10.5.0", "mode": "one_task_id_multiple_role_views"},
        "taskActionSurface": {"version": "10.6.0", "rule": "任务卡只展示一个主按钮和一个次按钮；详情不是流程动作。"},
        "acceptanceSurface": {"version": "10.9.0", "rule": "任务池必须能承接标签变化任务、跨账号视图和极简动作验收。"},
        "rule": "任务按当前账号投射角色视图，并把动作压缩成最小可操作集合。",
    }


@router.get("/todo/events")
def todo_events(request: Request) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    query_viewer_id = _viewer_for_query(viewer_id)
    return {"version": "10.9.0", "events": list_task_events_for_user(query_viewer_id), "counters": get_task_counters_for_user(query_viewer_id), "viewer": current_user(viewer_id)}


@router.get("/todo/counters")
def todo_counters(request: Request) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    query_viewer_id = _viewer_for_query(viewer_id)
    return {"version": "10.9.0", "counters": get_task_counters_for_user(query_viewer_id), "viewer": current_user(viewer_id)}


@router.get("/todo/{task_id}/evidence")
def todo_evidence(request: Request, task_id: str) -> Dict[str, Any]:
    evidence = get_task_evidence(task_id, viewer_id=request_user_id(request))
    if not evidence:
        raise HTTPException(status_code=404, detail="task evidence not found")
    evidence["crossAccountFlowVersion"] = "10.5.0"
    evidence["taskActionVersion"] = "10.6.0"
    evidence["acceptanceSurfaceVersion"] = "10.9.0"
    return evidence


@router.post("/todo/{task_id}/split")
def split_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"assign_tasks", "dispatch_tasks"})
    body = body or {}
    payload = {"assigneeId": body.get("operator_id") or body.get("operatorId") or body.get("assignee_id") or body.get("assigneeId"), "reviewerId": body.get("reviewer_id") or body.get("reviewerId"), "note": body.get("note") or "", "actorUserId": viewer_id}
    result = transition_task_with_repository(task_id, "manager_assigned", payload, ctx)
    return _task_from_write_result(result, error_detail="cannot split task", viewer_id=viewer_id)


@router.post("/todo/{task_id}/assign")
def assign_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"assign_tasks", "dispatch_tasks"})
    body = body or {}
    payload = {"assigneeId": body.get("assignee_id") or body.get("assigneeId"), "reviewerId": body.get("reviewer_id") or body.get("reviewerId"), "note": body.get("note") or "", "actorUserId": body.get("operator_id") or body.get("operatorId") or viewer_id}
    result = transition_task_with_repository(task_id, "manager_assigned", payload, ctx)
    return _task_from_write_result(result, error_detail="cannot assign task", viewer_id=viewer_id)


@router.post("/todo/{task_id}/accept")
def accept_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"submit_tasks", "handle_tasks", "assign_tasks", "dispatch_tasks"})
    body = body or {}
    result = transition_task_with_repository(task_id, "operator_accepted", {"note": body.get("note") or "", "actorUserId": viewer_id}, ctx)
    return _task_from_write_result(result, error_detail="cannot accept task", viewer_id=viewer_id)


@router.post("/todo/{task_id}/submit")
def submit_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"submit_tasks", "dispatch_tasks", "assign_tasks"})
    body = body or {}
    result = transition_task_with_repository(task_id, "operator_submitted", {"note": body.get("note") or "", "actorUserId": body.get("submitter_id") or body.get("submitterId") or viewer_id}, ctx)
    return _task_from_write_result(result, error_detail="cannot submit task", viewer_id=viewer_id)


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
    note = body.get("note") or ""
    action = "manager_returned" if decision in {"return", "reject", "rejected", "退回", "拒绝"} else "manager_approved"
    result = transition_task_with_repository(task_id, action, {"note": note, "actorUserId": body.get("reviewer_id") or body.get("reviewerId") or viewer_id}, ctx)
    task = _task_from_write_result(result, error_detail="cannot review task", viewer_id=viewer_id)
    if decision in {"approve", "approved", "pass", "通过"}:
        memory_draft = draft_experience_from_task(task_id, operator_submission=task.get("submissionNote") or "运营提交内容待补充。", manager_review=task.get("reviewNote") or note or "总管复核通过，待确认是否沉淀经验。", before_metrics=body.get("beforeMetrics") or body.get("before_metrics") or task.get("beforeMetrics") or {}, after_metrics=body.get("afterMetrics") or body.get("after_metrics") or task.get("afterMetrics") or {}, user_id=viewer_id)
        task["feedbackDraft"] = memory_draft
        task["feedbackRule"] = "V4.4 自动生成经验卡草案，但仍需老板 / 总管在 RAG Memory 中确认入库。"
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
    payload = {"recapTarget": body.get("recap_target") or body.get("recapTarget") or "日报", "note": body.get("note") or "", "actorUserId": viewer_id}
    result = transition_task_with_repository(task_id, "task_written_to_recap", payload, ctx)
    return _task_from_write_result(result, error_detail="cannot write task to recap", viewer_id=viewer_id)


@router.post("/todo/{task_id}/complete")
def complete_todo(request: Request, task_id: str, ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"review_tasks", "submit_tasks", "dispatch_tasks", "assign_tasks"})
    result = transition_task_with_repository(task_id, "task_completed", {"actorUserId": viewer_id}, ctx)
    return _task_from_write_result(result, error_detail="task not found", viewer_id=viewer_id)


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
