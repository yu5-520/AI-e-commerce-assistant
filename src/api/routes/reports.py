"""Report Center routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from src.repositories.sqlite_repository import list_report_records
from src.services.workflow_service import get_demo_report_text, run_full_workflow

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("")
def list_reports() -> Dict[str, Any]:
    records = list_report_records()
    if records:
        return {"reports": records}
    result = run_full_workflow(write_outputs=True, record_logs=True)
    return {"reports": [result.get("report_record", {})]}


@router.get("/demo", response_class=PlainTextResponse)
def demo_report() -> str:
    return get_demo_report_text()
