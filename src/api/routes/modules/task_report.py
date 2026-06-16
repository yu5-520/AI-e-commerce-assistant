"""Independent task report routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from src.services.task_report_service import get_candidate_report, get_task_report

router = APIRouter()


@router.get("/task-reports/tasks/{task_id}")
def task_report(task_id: str) -> Dict[str, Any]:
    report = get_task_report(task_id)
    if not report:
        raise HTTPException(status_code=404, detail="task report not found")
    return report


@router.get("/task-reports/candidates/{module}/{entity_id}")
def candidate_report(module: str, entity_id: str) -> Dict[str, Any]:
    report = get_candidate_report(module, entity_id)
    if not report:
        raise HTTPException(status_code=404, detail="candidate report not found")
    return report
