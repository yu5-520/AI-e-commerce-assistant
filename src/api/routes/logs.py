"""WorkflowRun and ExecutionLog routes."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

from src.services.log_service import (
    list_execution_logs,
    list_execution_logs_by_run,
    list_workflow_runs,
)

router = APIRouter(prefix="/api/logs", tags=["logs"])


def apply_run_filters(
    records: List[Dict[str, Any]],
    workflow_type: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    filtered = records
    if workflow_type:
        filtered = [item for item in filtered if item.get("workflow_type") == workflow_type]
    if status:
        filtered = [item for item in filtered if item.get("status") == status]
    return filtered


def apply_log_filters(
    records: List[Dict[str, Any]],
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    if status:
        return [item for item in records if item.get("status") == status]
    return records


@router.get("/workflow-runs")
def workflow_runs(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    workflow_type: Optional[str] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """List recent WorkflowRun records with simple pagination and filters."""
    records = list_workflow_runs(limit=1000)
    records = apply_run_filters(records, workflow_type=workflow_type, status=status)
    total = len(records)
    return {
        "items": records[offset : offset + limit],
        "total": total,
        "limit": limit,
        "offset": offset,
        "filters": {
            "workflow_type": workflow_type,
            "status": status,
        },
    }


@router.get("/execution-logs")
def execution_logs(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """List recent ExecutionLog records with simple pagination and status filter."""
    records = list_execution_logs(limit=1000)
    records = apply_log_filters(records, status=status)
    total = len(records)
    return {
        "items": records[offset : offset + limit],
        "total": total,
        "limit": limit,
        "offset": offset,
        "filters": {"status": status},
    }


@router.get("/workflow-runs/{workflow_run_id}/execution-logs")
def execution_logs_for_run(
    workflow_run_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """List ExecutionLog records for a specific WorkflowRun."""
    records = list_execution_logs_by_run(workflow_run_id=workflow_run_id, limit=1000)
    records = apply_log_filters(records, status=status)
    total = len(records)
    return {
        "items": records[offset : offset + limit],
        "total": total,
        "limit": limit,
        "offset": offset,
        "filters": {"status": status},
        "workflow_run_id": workflow_run_id,
    }
