"""Todo module routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException, Query, Request

from src.services.account_service import current_user, user_has_permission, user_id_from_headers
from src.services.module_task_service import (
    assign_task,
    complete_task,
    list_tasks,
    pin_task,
    reorder_task,
    reset_tasks,
    review_task,
    submit_task,
)

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
        "scope": scope,
        "viewer": current_user(viewer_id),
    }


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


@router.post("/todo/{task_id}/submit")
def submit_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"submit_tasks"})
    body = body or {}
    task = submit_task(
        task_id,
        note=body.get("note") or "",
        submitter_id=body.get("submitter_id") or body.get("submitterId") or viewer_id,
    )
    if not task:
        raise HTTPException(status_code=400, detail="cannot submit task")
    return task


@router.post("/todo/{task_id}/review")
def review_todo(request: Request, task_id: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"review_tasks"})
    body = body or {}
    task = review_task(
        task_id,
        decision=body.get("decision") or "approve",
        note=body.get("note") or "",
        reviewer_id=body.get("reviewer_id") or body.get("reviewerId") or viewer_id,
    )
    if not task:
        raise HTTPException(status_code=400, detail="cannot review task")
    return task


@router.post("/todo/{task_id}/complete")
def complete_todo(request: Request, task_id: str) -> Dict[str, Any]:
    viewer_id = request_user_id(request)
    require_any_permission(viewer_id, {"review_tasks", "submit_tasks"})
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
