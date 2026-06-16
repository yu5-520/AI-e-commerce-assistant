"""Todo module routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException, Query

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


@router.get("/todo")
def todo(
    scope: str = Query(default="all"),
    assignee_id: str | None = Query(default=None),
) -> Dict[str, Any]:
    review_scope = scope == "review"
    mine_assignee = assignee_id if scope in {"mine", "operator"} else None
    return {
        "tasks": list_tasks(assignee_id=mine_assignee, review_scope=review_scope),
        "activeTasks": list_tasks(active_only=True, assignee_id=mine_assignee, review_scope=review_scope),
        "scope": scope,
    }


@router.post("/todo/{task_id}/assign")
def assign_todo(task_id: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    task = assign_task(
        task_id,
        assignee_id=body.get("assignee_id") or body.get("assigneeId"),
        reviewer_id=body.get("reviewer_id") or body.get("reviewerId"),
        operator_id=body.get("operator_id") or body.get("operatorId"),
        note=body.get("note") or "",
    )
    if not task:
        raise HTTPException(status_code=400, detail="cannot assign task")
    return task


@router.post("/todo/{task_id}/submit")
def submit_todo(task_id: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    task = submit_task(
        task_id,
        note=body.get("note") or "",
        submitter_id=body.get("submitter_id") or body.get("submitterId"),
    )
    if not task:
        raise HTTPException(status_code=400, detail="cannot submit task")
    return task


@router.post("/todo/{task_id}/review")
def review_todo(task_id: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    task = review_task(
        task_id,
        decision=body.get("decision") or "approve",
        note=body.get("note") or "",
        reviewer_id=body.get("reviewer_id") or body.get("reviewerId"),
    )
    if not task:
        raise HTTPException(status_code=400, detail="cannot review task")
    return task


@router.post("/todo/{task_id}/complete")
def complete_todo(task_id: str) -> Dict[str, Any]:
    task = complete_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@router.post("/todo/{task_id}/pin")
def pin_todo(task_id: str) -> Dict[str, Any]:
    task = pin_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@router.post("/todo/{task_id}/reorder")
def reorder_todo(task_id: str, direction: str = "down") -> Dict[str, Any]:
    task = reorder_task(task_id, direction)
    if not task:
        raise HTTPException(status_code=400, detail="cannot reorder task")
    return task


@router.post("/todo/reset")
def reset_todo() -> Dict[str, Any]:
    return reset_tasks()
