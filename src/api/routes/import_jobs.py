"""ImportJob routes for report imports."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from src.core.context import UserContext, get_current_context
from src.services.import_job_service import get_import_job, list_import_jobs, run_import_job
from src.services.report_alert_service import import_report_dataset, run_v3_mock_imports
from src.services.report_schema_service import confirm_report_import

router = APIRouter(prefix="/api/data/import-jobs", tags=["import-jobs"])


@router.get("")
def import_jobs(limit: int = Query(default=50, ge=1, le=200), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """List ImportJob records scoped by current tenant."""

    return list_import_jobs(ctx, limit=limit)


@router.get("/{import_job_id}")
def import_job_detail(import_job_id: str, ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Return one ImportJob with its ProjectionJob records."""

    result = get_import_job(ctx, import_job_id)
    if not result:
        raise HTTPException(status_code=404, detail="import job not found")
    return result


@router.post("/confirm")
def confirm_import_job(body: Dict[str, Any] = Body(default_factory=dict), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Confirm report import through ImportJob wrapper."""

    dataset_name = body.get("dataset_name") or body.get("datasetName")
    if not dataset_name:
        raise HTTPException(status_code=400, detail="dataset_name is required")
    try:
        return run_import_job(
            ctx,
            dataset_name=str(dataset_name),
            source_type="confirm_report_import",
            payload=body,
            runner=lambda: confirm_report_import(
                str(dataset_name),
                rows=body.get("rows"),
                field_mapping=body.get("field_mapping") or body.get("fieldMapping"),
                auto_create_tasks=body.get("auto_create_tasks", body.get("autoCreateTasks", True)) is not False,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/report")
def report_import_job(body: Dict[str, Any] = Body(default_factory=dict), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Import report payload through ImportJob wrapper."""

    dataset_name = body.get("dataset_name") or body.get("datasetName")
    if not dataset_name:
        raise HTTPException(status_code=400, detail="dataset_name is required")
    try:
        return run_import_job(
            ctx,
            dataset_name=str(dataset_name),
            source_type="import_report_dataset",
            payload=body,
            runner=lambda: import_report_dataset(
                str(dataset_name),
                rows=body.get("rows"),
                auto_create_tasks=body.get("auto_create_tasks", body.get("autoCreateTasks", True)) is not False,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/mock-alerts")
def mock_alert_import_job(body: Dict[str, Any] = Body(default_factory=dict), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Run mock report imports through ImportJob wrapper."""

    dataset_names = body.get("dataset_names") or body.get("datasetNames")
    try:
        return run_import_job(
            ctx,
            dataset_name="mock-alerts",
            source_type="run_v3_mock_imports",
            payload=body,
            runner=lambda: run_v3_mock_imports(dataset_names=dataset_names),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
