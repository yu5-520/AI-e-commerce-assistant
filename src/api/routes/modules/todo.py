"""Todo module routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException, Query, Request

from src.services.account_service import current_user, user_has_permission, user_id_from_headers
from src.services.experience_memory_service import draft_experience_from_task
from src.services.module_task_service import (
    accept_task,
    assign_task,
    complete_task,
    get_task_counters_for_user,
    list_task_events_for_user,
    list_tasks,
    pin_task,
    reorder_task,
    reset_tasks,
    review_task,
    split_task_for_operator,
    submit_task,
    write_task_to_recap,
)
from src.services.task_evidence_service import get_task_evidence, review_task_evidence, submit_task_evidence

router = APIRouter()


def request_user_id(request: Request) -> str:
    return user_id_from_headers(request.headers)


def require_any_permission(user_id: str, permissions: set[str]) -> None:
    if not any(user_has_permission(user_id, permission) for permission in permissions):
        user = current_user(user_id)
        raise HTTPException(status_code=403, detail=f"{user['roleName']} does not have permission for this action")


@router.get("/todo")
def todo(
    request: Request,
    scope: str = Query(default="all"),
    assignee_id: str | None = Query(default=None),
) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    review_scope = scope == "review"
    mine_assignee = assignee_id if scope in {"mine", "operator"} else None
    return {
        "tasks": list_tasks(assignee_id=mine_assignee, review_scope=review_scope, viewer_id=viewer_id),
        "activeTasks": list_tasks(active_only=True, assignee_id=mine_assignee, review_scope=review_scope, viewer_id=viewer_id),
        "events": list_task_events_for_user(viewer_id),
        "counters": get_task_counters_for_user(viewer_id),
        "scope": scope,
        "viewer": current_user(viewer_id),
        "rule": "任务按当前账号的角色、店铺权限、负责人、复核人和可见范围过滤；动作会生成生命周期事件并同步相关账号视图。",
    }


@router.get("/todo/events")
def todo_events(request: Request) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    return {"events": list_task_events_for_user(viewer_id), "counters": get_task_counters_for_user(viewer_id), "viewer": current_user(viewer_id)}


@router.get("/todo/counters")
def todo_counters(request: Request) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    return {"counters": get_task_counters_for_user(viewer_id), "viewer": current_user(viewer_id)}


@router.get("/todo/{task_id}/evidence")
def todo_evidence(request: Request, task_id: str) -> Dict[str, Any]:
    evidence = get_task_evidence(task_id, viewer_id=request_user_id(request))
    if not evidence:
        raise HTTPException(status_code=404, detail="task evidence not found")
    return evidence


@router.post("/todo/{task_id}/split")
def split_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"assign_tasks", "dispatch_tasks"})
    body = body or {}
    task = split_task_for_operator(
        task_id,
        operator_id=body.get("operator_id") or body.get("operatorId") or body.get("assignee_id") or body.get("assigneeId"),
        note=body.get("note") or "",
        actor_user_id=viewer_id,
    )
    if not task:
        raise HTTPException(status_code=400, detail="cannot split task")
    return task


@router.post("/todo/{task_id}/assign")
def assign_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"assign_tasks", "dispatch_tasks"})
    body = body or {}
    task = assign_task(
        task_id,
        assignee_id=body.get("assignee_id") or body.get("assigneeId"),
        reviewer_id=body.get("reviewer_id") or body.get("reviewerId"),
        operator_id=body.get("operator_id") or body.get("operatorId") or viewer_id,
        note=body.get("note") or "",
    )
    if not task:
        raise HTTPException(status_code=400, detail="cannot assign task")
    return task


@router.post("/todo/{task_id}/accept")
def accept_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"submit_tasks", "handle_tasks", "assign_tasks", "dispatch_tasks"})
    body = body or {}
    task = accept_task(task_id, note=body.get("note") or "", actor_user_id=viewer_id)
    if not task:
        raise HTTPException(status_code=400, detail="cannot accept task")
    return task


@router.post("/todo/{task_id}/submit")
def submit_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"submit_tasks", "dispatch_tasks", "assign_tasks"})
    body = body or {}
    task = submit_task(
        task_id,
        note=body.get("note") or "",
        submitter_id=body.get("submitter_id") or body.get("submitterId") or viewer_id,
    )
    if not task:
        raise HTTPException(status_code=400, detail="cannot submit task")
    return task


@router.post("/todo/{task_id}/submit-evidence")
def submit_evidence_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"submit_tasks", "handle_tasks", "assign_tasks", "dispatch_tasks"})
    task = submit_task_evidence(task_id, body or {}, submitter_id=viewer_id)
    if not task:
        raise HTTPException(status_code=400, detail="cannot submit task evidence")
    return task


@router.post("/todo/{task_id}/review")
def review_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"review_tasks"})
    body = body or {}
    decision = body.get("decision") or "approve"
    note = body.get("note") or ""
    task = review_task(
        task_id,
        decision=decision,
        note=note,
        reviewer_id=body.get("reviewer_id") or body.get("reviewerId") or viewer_id,
    )
    if not task:
        raise HTTPException(status_code=400, detail="cannot review task")
    if decision in {"approve", "approved", "pass", "通过"}:
        memory_draft = draft_experience_from_task(
            task_id,
            operator_submission=task.get("submissionNote") or "运营提交内容待补充。",
            manager_review=task.get("reviewNote") or note or "总管复核通过，待确认是否沉淀经验。",
            before_metrics=body.get("beforeMetrics") or body.get("before_metrics") or task.get("beforeMetrics") or {},
            after_metrics=body.get("afterMetrics") or body.get("after_metrics") or task.get("afterMetrics") or {},
            user_id=viewer_id,
        )
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
    return task


@router.post("/todo/{task_id}/recap")
def recap_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"review_tasks", "assign_tasks", "dispatch_tasks"})
    body = body or {}
    task = write_task_to_recap(
        task_id,
        recap_target=body.get("recap_target") or body.get("recapTarget") or "日报",
        note=body.get("note") or "",
        actor_user_id=viewer_id,
    )
    if not task:
        raise HTTPException(status_code=400, detail="cannot write task to recap")
    return task


@router.post("/todo/{task_id}/complete")
def complete_todo(request: Request, task_id: str) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"review_tasks", "submit_tasks", "dispatch_tasks", "assign_tasks"})
    task = complete_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@router.post("/todo/{task_id}/pin")
def pin_todo(request: Request, task_id: str) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"assign_tasks", "dispatch_tasks"})
    task = pin_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@router.post("/todo/{task_id}/reorder")
def reorder_todo(request: Request, task_id: str, direction: str = "down") -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"assign_tasks", "dispatch_tasks"})
    task = reorder_task(task_id, direction)
    if not task:
        raise HTTPException(status_code=400, detail="cannot reorder task")
    return task


@router.post("/todo/reset")
def reset_todo(request: Request) -> Dict[str, Any]:
    return reset_tasks(viewer_id=request_user_id(request))
