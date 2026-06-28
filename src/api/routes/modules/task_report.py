"""Task report routes with fail-closed fallback."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request

from src.services.account_service import user_id_from_headers
from src.services.alert_detail_service import get_alert_detail_report
from src.services.task_report_service import get_candidate_report, get_task_report

router = APIRouter()
TASK_REPORT_ROUTE_VERSION = "12.8.1"


def request_user_id(request: Request) -> str:
    return user_id_from_headers(request.headers)


def _safe_report(kind: str, entity_id: str, exc: Exception) -> Dict[str, Any]:
    return {
        "id": entity_id,
        "title": "Detail report safe fallback",
        "version": TASK_REPORT_ROUTE_VERSION,
        "reportType": kind,
        "failClosed": True,
        "summary": "The task remains available. Report generation returned a structured fallback instead of HTTP 500.",
        "error": str(exc),
        "sections": [{"title": "Next step", "items": ["Refresh task list", "Use the task summary", "Retry detail report after refresh"]}],
    }


@router.get("/task-reports/tasks/{task_id}")
def task_report(request: Request, task_id: str) -> Dict[str, Any]:
    try:
        report = get_task_report(task_id, user_id=request_user_id(request))
    except Exception as exc:
        return _safe_report("task", task_id, exc)
    if not report:
        raise HTTPException(status_code=404, detail="task report not found")
    return report


@router.get("/task-reports/candidates/{module}/{entity_id}")
def candidate_report(request: Request, module: str, entity_id: str) -> Dict[str, Any]:
    try:
        report = get_candidate_report(module, entity_id, user_id=request_user_id(request))
    except Exception as exc:
        return _safe_report("candidate", f"{module}:{entity_id}", exc)
    if not report:
        raise HTTPException(status_code=404, detail="candidate report not found")
    return report


@router.get("/task-reports/alerts/{alert_id}")
def alert_report(request: Request, alert_id: str) -> Dict[str, Any]:
    try:
        report = get_alert_detail_report(alert_id, user_id=request_user_id(request))
    except Exception as exc:
        return _safe_report("alert", alert_id, exc)
    if not report:
        raise HTTPException(status_code=404, detail="alert report not found")
    return report
