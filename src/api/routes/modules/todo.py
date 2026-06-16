"""Todo module routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from src.services.module_task_service import complete_task, list_tasks, pin_task, reorder_task, reset_tasks

router = APIRouter()


@router.get("/todo")
def todo() -> Dict[str, Any]:
    return {"tasks": list_tasks(), "activeTasks": list_tasks(active_only=True)}


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
