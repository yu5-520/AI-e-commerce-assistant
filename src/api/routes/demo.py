"""Demo workflow routes kept for compatibility with the current frontend."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from src.services.approval_service import get_task_status_overrides
from src.services.workflow_service import get_demo_report_text, run_full_workflow

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.get("/run")
def run_demo_api() -> Dict[str, Any]:
    result = run_full_workflow(write_outputs=True)
    overrides = get_task_status_overrides()
    if overrides:
        result["task_status_overrides"] = overrides
    return result


@router.get("/report", response_class=PlainTextResponse)
def demo_report() -> str:
    return get_demo_report_text()
