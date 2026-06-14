"""WorkflowRun and ExecutionLog routes."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

from src.services.log_service import (
    list_execution_logs,
    list_execution_logs_by_run,
    list_workflow_runs,
)

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("/workflow-runs")
def workflow_runs() -> List[Dict[str, Any]]:
    """List recent WorkflowRun records."""
    return list_workflow_runs()


@router.get("/execution-logs")
def execution_logs() -> List[Dict[str, Any]]:
    """List recent ExecutionLog records."""
    return list_execution_logs()


@router.get("/workflow-runs/{workflow_run_id}/execution-logs")
def execution_logs_for_run(workflow_run_id: str) -> List[Dict[str, Any]]:
    """List ExecutionLog records for a specific WorkflowRun."""
    return list_execution_logs_by_run(workflow_run_id=workflow_run_id)
