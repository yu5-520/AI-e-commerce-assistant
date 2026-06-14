"""Task Center routes."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from src.services.approval_service import get_task_status_overrides
from src.services.workflow_service import get_approval_required_tasks, get_task, get_tasks

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("")
def list_tasks() -> List[Dict[str, Any]]:
    overrides = get_task_status_overrides()
    tasks = []
    for task in get_tasks():
        task_id = str(task.get("task_id"))
        tasks.append({**task, **overrides.get(task_id, {})})
    return tasks


@router.get("/approval-required")
def approval_required_tasks() -> List[Dict[str, Any]]:
    return get_approval_required_tasks()


@router.get("/status")
def task_status() -> Dict[str, Dict[str, Any]]:
    return get_task_status_overrides()


@router.get("/{task_id}")
def task_detail(task_id: str) -> Dict[str, Any]:
    task = get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    override = get_task_status_overrides().get(task_id, {})
    return {**task, **override}
