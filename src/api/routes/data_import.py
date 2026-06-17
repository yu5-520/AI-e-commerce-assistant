"""Data Hub routes."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Body, HTTPException, Query

from src.services.data_import_service import (
    import_mock_data,
    list_import_records,
    list_import_sources,
    validate_all_imports,
)
from src.services.report_alert_service import (
    get_v3_dashboard_summary,
    import_report_dataset,
    latest_data_version,
    list_alert_events,
    list_alerts_for_entity,
    list_data_versions,
    run_v3_mock_imports,
)
from src.services.report_schema_service import (
    confirm_report_import,
    get_report_templates,
    preview_report_dataset,
)

router = APIRouter(prefix="/api/data", tags=["data-import"])


@router.get("/sources")
def data_sources() -> List[Dict[str, Any]]:
    """List available Mock ERP / CRM import sources."""
    return list_import_sources()


@router.post("/validate")
def validate_imports() -> Dict[str, Any]:
    """Validate all Mock ERP / CRM datasets and relationship checks."""
    return validate_all_imports()


@router.post("/import/mock")
def import_mock() -> Dict[str, Any]:
    """Create an import record for current Mock datasets after validation."""
    return import_mock_data()


@router.get("/imports")
def imports() -> List[Dict[str, Any]]:
    """List recent import records."""
    return list_import_records()


@router.get("/templates")
def report_templates() -> Dict[str, Any]:
    """V3.0.2: return report field templates and alias hints."""
    return get_report_templates()


@router.post("/preview")
def preview_report(body: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    """V3.0.2: preview field mapping before creating alerts or tasks."""
    dataset_name = body.get("dataset_name") or body.get("datasetName")
    if not dataset_name:
        raise HTTPException(status_code=400, detail="dataset_name is required")
    try:
        return preview_report_dataset(
            str(dataset_name),
            rows=body.get("rows"),
            field_mapping=body.get("field_mapping") or body.get("fieldMapping"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/import/confirm")
def confirm_import(body: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    """V3.0.2: confirm a previewed report import, then trigger alerts/tasks."""
    dataset_name = body.get("dataset_name") or body.get("datasetName")
    if not dataset_name:
        raise HTTPException(status_code=400, detail="dataset_name is required")
    try:
        return confirm_report_import(
            str(dataset_name),
            rows=body.get("rows"),
            field_mapping=body.get("field_mapping") or body.get("fieldMapping"),
            auto_create_tasks=body.get("auto_create_tasks", body.get("autoCreateTasks", True)) is not False,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/import/report")
def import_report(body: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    """V3: import one report payload, create a data version, then trigger alerts.

    Expected body:
    {
      "dataset_name": "inventory" | "refunds" | "orders" | "products" | "customers",
      "rows": [{...}],              # optional; when omitted, reads examples/*.csv
      "auto_create_tasks": true     # default true
    }
    """
    dataset_name = body.get("dataset_name") or body.get("datasetName")
    if not dataset_name:
        raise HTTPException(status_code=400, detail="dataset_name is required")
    try:
        return import_report_dataset(
            str(dataset_name),
            rows=body.get("rows"),
            auto_create_tasks=body.get("auto_create_tasks", body.get("autoCreateTasks", True)) is not False,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/import/mock-alerts")
def import_mock_alerts(body: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    """V3: run report-driven alert generation from current examples/*.csv files."""
    dataset_names = body.get("dataset_names") or body.get("datasetNames")
    try:
        return run_v3_mock_imports(dataset_names=dataset_names)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/versions")
def data_versions(limit: int = Query(default=20, ge=1, le=100)) -> List[Dict[str, Any]]:
    """V3: list recent data snapshots created by report imports."""
    return list_data_versions(limit=limit)


@router.get("/versions/latest")
def latest_version() -> Dict[str, Any]:
    """V3: return the latest data version used by global warning refresh."""
    latest = latest_data_version()
    return latest or {"version": "3.0.2", "message": "No V3 data snapshot has been imported yet."}


@router.get("/alerts")
def alerts(
    limit: int = Query(default=50, ge=1, le=200),
    active_only: bool = Query(default=False),
) -> List[Dict[str, Any]]:
    """V3: list report-triggered alert events."""
    return list_alert_events(limit=limit, active_only=active_only)


@router.get("/alerts/entity/{entity_type}/{entity_id}")
def entity_alerts(entity_type: str, entity_id: str) -> List[Dict[str, Any]]:
    """V3: list alert events for one product/customer/entity."""
    return list_alerts_for_entity(entity_type, entity_id)


@router.get("/v3-summary")
def v3_summary() -> Dict[str, Any]:
    """V3: global data-version and alert summary for homepage sync."""
    return get_v3_dashboard_summary()
