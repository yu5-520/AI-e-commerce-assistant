"""Report Center routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from src.services.workflow_service import get_demo_report_text, run_full_workflow

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("")
def list_reports() -> Dict[str, Any]:
    result = run_full_workflow(write_outputs=True)
    return {
        "reports": [
            {
                "report_id": "demo_report",
                "report_type": "mock_workflow_report",
                "format": "markdown",
                "path": result.get("report_path"),
            }
        ]
    }


@router.get("/demo", response_class=PlainTextResponse)
def demo_report() -> str:
    return get_demo_report_text()
