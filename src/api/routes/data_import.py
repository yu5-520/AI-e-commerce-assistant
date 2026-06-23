"""Data Hub routes."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Body, HTTPException, Query, Request

from src.services.account_service import current_user, user_id_from_headers
from src.services.data_import_service import (
    import_mock_data,
    list_import_records,
    list_import_sources,
    validate_all_imports,
)
from src.services.data_version_service import delete_data_version, get_data_version_detail
from src.services.data_version_service import list_import_records as list_version_import_records
from src.services.data_version_service import rollback_data_version
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
    normalize_rows_with_mapping,
    preview_report_dataset,
)
from src.services.trend_signal_service import ingest_product_trends

router = APIRouter(prefix="/api/data", tags=["data-import"])
ROLLBACK_ROLE_IDS = {"owner", "manager", "finance"}


def request_user_id(request: Request) -> str:
    return user_id_from_headers(request.headers)


def can_rollback(user_id: str) -> bool:
    user = current_user(user_id)
    return user.get("roleId") in ROLLBACK_ROLE_IDS


def require_rollback_permission(user_id: str) -> None:
    if not can_rollback(user_id):
        raise HTTPException(status_code=403, detail="当前账号无权回滚全局数据版本")


def _attach_v61_trend_sync(result: Dict[str, Any], rows: Any, source_system: str | None = None) -> Dict[str, Any]:
    """Generate product snapshots, metric trends, and business signals after import."""
    if not isinstance(rows, list):
        result["trendSync"] = {"version": "6.1.0", "skipped": True, "reason": "rows is not a list"}
        return result
    import_results = result.get("results") if isinstance(result.get("results"), list) else [result]
    summaries: List[Dict[str, Any]] = []
    for item in import_results:
        if not isinstance(item, dict):
            continue
        dataset_name = item.get("datasetName")
        data_version = item.get("dataVersion")
        if not dataset_name or not data_version:
            continue
        field_mapping = (item.get("schemaPreview") or {}).get("fieldMapping") or {}
        routed_rows = normalize_rows_with_mapping(rows, field_mapping) if isinstance(field_mapping, dict) else rows
        trend_summary = ingest_product_trends(
            dataset_name=str(dataset_name),
            data_version=str(data_version),
            rows=routed_rows,
            source_system=source_system or result.get("sourceSystem"),
        )
        item["trendSync"] = trend_summary
        summaries.append(trend_summary)
    result["trendSync"] = {
        "version": "6.1.0",
        "mode": "product_snapshot_metric_trend_signal_sync",
        "datasetCount": len(summaries),
        "snapshotCount": sum(item.get("snapshotCount", 0) for item in summaries),
        "trendCount": sum(item.get("trendCount", 0) for item in summaries),
        "signalCount": sum(item.get("signalCount", 0) for item in summaries),
        "taskCandidateSignalCount": sum(item.get("taskCandidateSignalCount", 0) for item in summaries),
        "summaries": summaries,
        "rule": "V6.1 导入后生成商品时间快照、指标变化和经营信号；V6.2 再接风险分级任务。",
    }
    return result


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


@router.get("/import-records")
def import_records(limit: int = Query(default=50, ge=1, le=200)) -> Dict[str, Any]:
    """List report data versions with alert/task impact and rollback state."""
    return list_version_import_records(limit=limit)


@router.get("/versions/{data_version}/detail")
def version_detail(request: Request, data_version: str) -> Dict[str, Any]:
    """Return one data version detail with alerts, linked tasks, rollback, and permissions."""
    user_id = request_user_id(request)
    try:
        detail = get_data_version_detail(data_version, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    detail["permissions"] = {
        "canRollback": can_rollback(user_id) and bool(detail.get("record", {}).get("canRollback")),
        "canDelete": True,
        "rollbackRoleIds": sorted(ROLLBACK_ROLE_IDS),
    }
    return detail


@router.post("/versions/{data_version}/rollback")
def rollback_version(request: Request, data_version: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    """Soft-rollback alerts generated by one report data version and handle linked tasks."""
    body = body or {}
    user_id = request_user_id(request)
    require_rollback_permission(user_id)
    try:
        return rollback_data_version(
            data_version,
            operator_id=user_id,
            reason=body.get("reason") or body.get("note"),
            task_strategy=body.get("task_strategy") or body.get("taskStrategy") or "review",
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/versions/{data_version}")
def delete_version(
    request: Request,
    data_version: str,
    confirm: bool = Query(default=False),
    body: Dict[str, Any] | None = Body(default=None),
) -> Dict[str, Any]:
    """Hard-delete one demo data version so test imports do not keep stacking."""
    if not confirm:
        raise HTTPException(status_code=400, detail="删除导入记录需要 confirm=true")
    body = body or {}
    user_id = request_user_id(request)
    try:
        return delete_data_version(
            data_version,
            operator_id=user_id,
            reason=body.get("reason") or body.get("note") or "Demo 阶段删除导入记录。",
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/templates")
def report_templates() -> Dict[str, Any]:
    """Return report field templates and alias hints."""
    return get_report_templates()


@router.post("/preview")
def preview_report(body: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    """Preview field mapping before creating alerts or tasks."""
    dataset_name = body.get("dataset_name") or body.get("datasetName")
    if not dataset_name:
        raise HTTPException(status_code=400, detail="dataset_name is required")
    try:
        return preview_report_dataset(
            str(dataset_name),
            rows=body.get("rows"),
            field_mapping=body.get("field_mapping") or body.get("fieldMapping"),
            source_system=body.get("source_system") or body.get("sourceSystem"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/import/confirm")
def confirm_import(body: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    """Confirm a previewed report import, then trigger scoped alerts/tasks and V6.1 trends."""
    dataset_name = body.get("dataset_name") or body.get("datasetName")
    if not dataset_name:
        raise HTTPException(status_code=400, detail="dataset_name is required")
    source_system = body.get("source_system") or body.get("sourceSystem")
    try:
        result = confirm_report_import(
            str(dataset_name),
            rows=body.get("rows"),
            field_mapping=body.get("field_mapping") or body.get("fieldMapping"),
            auto_create_tasks=body.get("auto_create_tasks", body.get("autoCreateTasks", True)) is not False,
            source_system=source_system,
        )
        return _attach_v61_trend_sync(result, body.get("rows"), source_system=source_system)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/import/report")
def import_report(body: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    """Import one report payload, create a data version, then trigger scoped alerts."""
    dataset_name = body.get("dataset_name") or body.get("datasetName")
    if not dataset_name:
        raise HTTPException(status_code=400, detail="dataset_name is required")
    try:
        result = import_report_dataset(
            str(dataset_name),
            rows=body.get("rows"),
            auto_create_tasks=body.get("auto_create_tasks", body.get("autoCreateTasks", True)) is not False,
        )
        return _attach_v61_trend_sync(result, body.get("rows"), source_system=body.get("source_system") or body.get("sourceSystem"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/import/mock-alerts")
def import_mock_alerts(body: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    """Run report-driven alert generation from current examples/*.csv files."""
    dataset_names = body.get("dataset_names") or body.get("datasetNames")
    try:
        return run_v3_mock_imports(dataset_names=dataset_names)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/versions")
def data_versions(limit: int = Query(default=20, ge=1, le=100)) -> List[Dict[str, Any]]:
    """List recent data snapshots created by report imports."""
    return list_data_versions(limit=limit)


@router.get("/versions/latest")
def latest_version() -> Dict[str, Any]:
    """Return the latest data version used by global warning refresh."""
    latest = latest_data_version()
    return latest or {"version": "6.1.0", "message": "No data snapshot has been imported yet."}


@router.get("/alerts")
def alerts(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    active_only: bool = Query(default=False),
) -> List[Dict[str, Any]]:
    """List report-triggered alert events scoped by current account store access."""
    return list_alert_events(limit=limit, active_only=active_only, user_id=request_user_id(request))


@router.get("/alerts/entity/{entity_type}/{entity_id}")
def entity_alerts(request: Request, entity_type: str, entity_id: str) -> List[Dict[str, Any]]:
    """List alert events for one product/customer/entity scoped by current account."""
    return list_alerts_for_entity(entity_type, entity_id, user_id=request_user_id(request))


@router.get("/v3-summary")
def v3_summary(request: Request) -> Dict[str, Any]:
    """Global data-version and alert summary scoped by current account."""
    return get_v3_dashboard_summary(request_user_id(request))
