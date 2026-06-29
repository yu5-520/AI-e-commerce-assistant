"""V14.2 Data Hub routes.

Import endpoints still write facts, objects and snapshots first. After that they run
V14.2 snapshot-driven task mainline so uploaded reports do not depend on front-end
refresh to create signals and tasks.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from fastapi import APIRouter, Body, File, Form, HTTPException, Query, Request, UploadFile

from src.core.context import context_from_headers
from src.services.account_service import current_user, user_id_from_headers
from src.services.data_gap_event_service import data_gap_summary, ingest_data_gaps_from_import
from src.services.data_import_service import DATASET_CONFIGS, import_mock_data, list_import_records, list_import_sources, read_csv, validate_all_imports
from src.services.data_source_connection_service import build_source_sync_summary, get_data_source_connection, list_data_source_connections
from src.services.data_version_service import delete_data_version, get_data_version_detail
from src.services.data_version_service import list_import_records as list_version_import_records
from src.services.data_version_service import rollback_data_version
from src.services.import_adapter_service import compact_upload_meta, parse_upload_file
from src.services.import_diagnostics_service import import_diagnostics
from src.services.metric_fact_store_service import ingest_metric_facts_from_import, ingest_metric_facts_from_sheet_rows, metric_fact_summary
from src.services.operating_object_store_service import upsert_operating_objects_from_import
from src.services.operating_unit_snapshot_service import materialize_operating_unit_snapshot
from src.services.pipeline_gate_service import record_stage_gate
from src.services.report_alert_service import get_v3_dashboard_summary, import_report_dataset, list_alert_events, list_alerts_for_entity
from src.services.report_schema_service import confirm_report_import, get_report_templates, preview_report_dataset
from src.services.v142_task_mainline_service import run_v142_task_mainline

router = APIRouter(prefix="/api/data", tags=["data-import"])
ROLLBACK_ROLE_IDS = {"owner", "manager", "finance"}
DEFAULT_SYNC_DATASETS = ["inventory", "refunds", "orders", "products"]
DATA_IMPORT_ROUTE_VERSION = "14.2.0"


def request_user_id(request: Request) -> str:
    return user_id_from_headers(request.headers)


def can_rollback(user_id: str) -> bool:
    return current_user(user_id).get("roleId") in ROLLBACK_ROLE_IDS


def require_rollback_permission(user_id: str) -> None:
    if not can_rollback(user_id):
        raise HTTPException(status_code=403, detail="当前账号无权回滚全局数据版本")


def _dataset_rows(dataset_name: str | None) -> List[Dict[str, Any]]:
    config = DATASET_CONFIGS.get(str(dataset_name or "").strip())
    if not config:
        return []
    try:
        return [{str(key): value for key, value in row.items()} for row in read_csv(str(config["filename"]))]
    except Exception:
        return []


def _normalize_result_rows(item: Dict[str, Any], rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    dataset_name = item.get("datasetName")
    data_version = item.get("dataVersion")
    normalized: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        next_row = {str(key): value for key, value in row.items()}
        if dataset_name:
            next_row.setdefault("datasetName", dataset_name)
        if data_version:
            next_row.setdefault("dataVersion", data_version)
        normalized.append(next_row)
    return normalized


def _materialize_import_rows(result: Dict[str, Any], rows: Any = None) -> List[Dict[str, Any]]:
    if isinstance(rows, list) and rows:
        return _normalize_result_rows(result, rows)
    results = result.get("results") if isinstance(result.get("results"), list) else [result]
    all_rows: List[Dict[str, Any]] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        item_rows = item.get("rows") if isinstance(item.get("rows"), list) else None
        if not item_rows:
            item_rows = item.get("sampleRows") if isinstance(item.get("sampleRows"), list) else None
        if not item_rows:
            item_rows = _dataset_rows(item.get("datasetName"))
        normalized = _normalize_result_rows(item, item_rows or [])
        if normalized:
            item["rows"] = normalized
            all_rows.extend(normalized)
    if all_rows:
        result["rows"] = all_rows
    return all_rows


def _run_dataset_imports_without_legacy_tasks(dataset_names: Iterable[str] | None = None) -> Dict[str, Any]:
    selected = [str(name) for name in (dataset_names or DEFAULT_SYNC_DATASETS)]
    results: List[Dict[str, Any]] = []
    all_rows: List[Dict[str, Any]] = []
    for name in selected:
        rows = _dataset_rows(name)
        result = import_report_dataset(name, rows=rows, auto_create_tasks=False)
        normalized = _normalize_result_rows(result, rows)
        result["rows"] = normalized
        result["legacyTaskCreationDisabled"] = True
        result["rule"] = "V14.2：接口同步只写事实、经营对象和快照；任务生成由V14.2快照主链触发。"
        results.append(result)
        all_rows.extend(normalized)
    return {"version": DATA_IMPORT_ROUTE_VERSION, "mode": "dataset_sync_without_legacy_task_triggers", "datasetCount": len(results), "rowCount": len(all_rows), "alertCount": sum(item.get("alertCount", 0) for item in results), "createdTaskCount": 0, "taggedAlertCount": sum(item.get("taggedAlertCount", 0) for item in results), "results": results, "rows": all_rows, "summary": get_v3_dashboard_summary(), "rule": "导入先完成数据站点；任务生成走V14.2系统快照主链。"}


def _attach_operating_object_sync(request: Request, result: Dict[str, Any], rows: Any, *, source: str) -> Dict[str, Any]:
    materialized_rows = _materialize_import_rows(result, rows)
    if materialized_rows:
        result["rows"] = materialized_rows
    ctx = context_from_headers(request.headers)
    result["operatingObjectSync"] = upsert_operating_objects_from_import(result, materialized_rows, source=source, uploader_user_id=ctx.user_id, uploader_role_id=ctx.role_id)
    return result


def _report_profile_from_result(result: Dict[str, Any]) -> Dict[str, Any] | None:
    upload_meta = result.get("uploadMeta") if isinstance(result.get("uploadMeta"), dict) else {}
    profile = upload_meta.get("reportProfile") if isinstance(upload_meta, dict) else None
    return profile if isinstance(profile, dict) else result.get("reportProfile") if isinstance(result.get("reportProfile"), dict) else None


def _attach_v121_metric_fact_sync(result: Dict[str, Any], rows: Any, *, source: str, source_system: str | None = None, parsed: Dict[str, Any] | None = None) -> Dict[str, Any]:
    materialized_rows = _materialize_import_rows(result, rows)
    if materialized_rows:
        result["rows"] = materialized_rows
    if parsed and isinstance(parsed.get("sheetRows"), dict) and parsed.get("sheetRows"):
        result["metricFactSync"] = ingest_metric_facts_from_sheet_rows(result, parsed, report_profile=_report_profile_from_result(result), source_system=source_system or result.get("sourceSystem"), source_report_id=source)
        return result
    if not materialized_rows:
        result["metricFactSync"] = {"version": DATA_IMPORT_ROUTE_VERSION, "skipped": True, "reason": "rows is not a list"}
        return result
    result["metricFactSync"] = ingest_metric_facts_from_import(result, materialized_rows, report_profile=_report_profile_from_result(result), source_system=source_system or result.get("sourceSystem"), source_report_id=source)
    return result


def _attach_v1213_data_gap_sync(result: Dict[str, Any], rows: Any, *, source: str, source_system: str | None = None, parsed: Dict[str, Any] | None = None) -> Dict[str, Any]:
    materialized_rows = _materialize_import_rows(result, rows)
    if materialized_rows:
        result["rows"] = materialized_rows
    parsed_payload = parsed if isinstance(parsed, dict) else {"rows": materialized_rows}
    result["dataGapSync"] = ingest_data_gaps_from_import(result, parsed_payload, report_profile=_report_profile_from_result(result), source_system=source_system or result.get("sourceSystem"), source_report_id=source)
    return result


def _data_versions_from_result(result: Dict[str, Any]) -> List[str]:
    versions: List[str] = []
    if result.get("dataVersion"):
        versions.append(str(result["dataVersion"]))
    for item in (result.get("results") if isinstance(result.get("results"), list) else []):
        if isinstance(item, dict) and item.get("dataVersion"):
            versions.append(str(item["dataVersion"]))
    return list(dict.fromkeys([item for item in versions if item]))


def _attach_pipeline_station_sync(request: Request, result: Dict[str, Any], *, source: str) -> Dict[str, Any]:
    ctx = context_from_headers(request.headers)
    versions = _data_versions_from_result(result) or [None]  # type: ignore[list-item]
    gates = []
    for version in versions:
        gate_input = {"source": source, "rowCount": len(result.get("rows") or []), "sourceSystem": result.get("sourceSystem")}
        gates.append(record_stage_gate(data_version=version, stage="import_uploaded", status="completed", input_payload=gate_input, output_payload={"dataVersion": version}, user_id=ctx.user_id, output_ref=f"import:{version or 'latest'}"))
        gates.append(record_stage_gate(data_version=version, stage="report_parsed", status="completed", input_payload=gate_input, output_payload={"rowCount": len(result.get("rows") or [])}, user_id=ctx.user_id, upstream_stage="import_uploaded", output_ref=f"rows:{version or 'latest'}"))
        gates.append(record_stage_gate(data_version=version, stage="metric_facts_ready", status="completed", input_payload={"metricFactSync": result.get("metricFactSync")}, output_payload={"summary": result.get("metricFactSync")}, user_id=ctx.user_id, upstream_stage="report_parsed", output_ref=f"metric_facts:{version or 'latest'}"))
        gates.append(record_stage_gate(data_version=version, stage="operating_objects_ready", status="completed", input_payload={"operatingObjectSync": result.get("operatingObjectSync")}, output_payload={"summary": result.get("operatingObjectSync")}, user_id=ctx.user_id, upstream_stage="metric_facts_ready", output_ref=f"operating_objects:{version or 'latest'}"))
        snapshot = materialize_operating_unit_snapshot(user_id=ctx.user_id, data_version=version, force=True)
        result["operatingUnitSnapshotSync"] = snapshot
        gates.append(record_stage_gate(data_version=version, stage="operating_unit_snapshot_ready", status="completed", input_payload={"source": source}, output_payload={"snapshotKey": snapshot.get("snapshotKey"), "storeCount": len(snapshot.get("storeRows") or [])}, user_id=ctx.user_id, upstream_stage="operating_objects_ready", output_ref=snapshot.get("snapshotKey")))
    result["pipelineSync"] = {"version": DATA_IMPORT_ROUTE_VERSION, "mode": "import_station_gates_then_v142_task_mainline", "dataVersions": [item for item in versions if item], "gateCount": len(gates), "gates": gates, "taskGeneration": "v142_mainline_after_import", "rule": "V14.2：上传/同步先到经营页快照站，再进入系统商品快照与商品信号快照主链。"}
    return result


def _attach_import_diagnostics(result: Dict[str, Any]) -> Dict[str, Any]:
    version = result.get("dataVersion")
    if not version and isinstance(result.get("results"), list) and result["results"]:
        version = next((item.get("dataVersion") for item in result["results"] if isinstance(item, dict) and item.get("dataVersion")), None)
    result["importDiagnostics"] = import_diagnostics(str(version) if version else None, report_profile=_report_profile_from_result(result), metric_fact_sync=result.get("metricFactSync") if isinstance(result.get("metricFactSync"), dict) else None, data_gap_sync=result.get("dataGapSync") if isinstance(result.get("dataGapSync"), dict) else None, risk_task_sync=None)
    return result


def _attach_import_product_contracts(request: Request, result: Dict[str, Any], rows: Any, *, source: str, upsert_objects: bool = True) -> Dict[str, Any]:
    if upsert_objects:
        result = _attach_operating_object_sync(request, result, rows, source=source)
        result = _attach_v121_metric_fact_sync(result, rows, source=source)
        result = _attach_v1213_data_gap_sync(result, rows, source=source)
    result["legacyImportTaskHooksDisabled"] = True
    result["legacyHooksRemoved"] = ["attach_v104_import_sync", "attach_v107_operating_profile", "attach_v108_tag_change_tasks", "attach_v116_import_closed_loop", "_attach_v62_trend_and_risk_sync"]
    result.setdefault("createdTaskCount", 0)
    result.setdefault("riskTaskSync", {"version": DATA_IMPORT_ROUTE_VERSION, "skipped": True, "reason": "task_generation_moved_to_v142_snapshot_mainline"})
    result["rule"] = "V14.2：导入接口保留旧任务隔绝，并触发系统商品快照主链。"
    return _attach_import_diagnostics(result)


def _attach_v142_task_mainline(request: Request, result: Dict[str, Any], *, source: str) -> Dict[str, Any]:
    ctx = context_from_headers(request.headers)
    versions = _data_versions_from_result(result)
    if not versions and result.get("dataVersion"):
        versions = [str(result["dataVersion"])]
    runs = []
    for version in versions:
        runs.append(run_v142_task_mainline(version, user_id=ctx.user_id, max_signals=50, force=True, source=source))
    result["v142TaskMainlineSync"] = {"version": DATA_IMPORT_ROUTE_VERSION, "runCount": len(runs), "runs": runs, "createdTaskCount": sum((run.get("taskGeneration") or {}).get("createdTaskCount", 0) for run in runs), "productSnapshotCount": sum((run.get("taskGeneration") or {}).get("productSnapshotCount", 0) for run in runs), "productSignalCount": sum((run.get("taskGeneration") or {}).get("productSignalCount", 0) for run in runs), "signalCount": sum((run.get("taskGeneration") or {}).get("signalCount", 0) for run in runs), "judgmentCount": sum((run.get("taskGeneration") or {}).get("judgmentCount", 0) for run in runs), "taskSnapshotCount": sum((run.get("taskGeneration") or {}).get("taskSnapshotCount", 0) for run in runs), "rule": "V14.2：上传后端自动执行系统商品快照→商品信号快照→RAG→Agent→任务快照→任务池。"}
    result["createdTaskCount"] = result["v142TaskMainlineSync"]["createdTaskCount"]
    return result


def _finalize_import(request: Request, result: Dict[str, Any], rows: Any, *, source: str, upsert_objects: bool = False) -> Dict[str, Any]:
    final = _attach_import_product_contracts(request, result, rows, source=source, upsert_objects=upsert_objects)
    return _attach_v142_task_mainline(request, final, source=source)


async def _rows_from_uploaded_file(file: UploadFile) -> Dict[str, Any]:
    content = await file.read()
    try:
        return parse_upload_file(file.filename or "upload", content, content_type=file.content_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/sources")
def data_sources() -> List[Dict[str, Any]]:
    return list_import_sources()


@router.get("/source-connections")
def data_source_connections() -> Dict[str, Any]:
    return {"version": DATA_IMPORT_ROUTE_VERSION, "sources": list_data_source_connections(), "rule": "数据源配置只读，不触发同步。"}


@router.post("/source-connections/{source_id}/sync")
def sync_source_connection(request: Request, source_id: str) -> Dict[str, Any]:
    try:
        source = get_data_source_connection(source_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if source.get("priority") == "backup":
        raise HTTPException(status_code=400, detail="手动上传是备用入口，请使用 /api/data/import/confirm 或前端文件上传。")
    result = _run_dataset_imports_without_legacy_tasks(source.get("datasetNames") or None)
    result["sourceConnection"] = build_source_sync_summary(source_id, result)
    result["dataSourceSync"] = result["sourceConnection"]
    objected = _attach_operating_object_sync(request, result, result.get("rows"), source=f"{source_id}_api_sync")
    facted = _attach_v121_metric_fact_sync(objected, objected.get("rows"), source=f"{source_id}_api_sync", source_system=source_id)
    gapped = _attach_v1213_data_gap_sync(facted, facted.get("rows"), source=f"{source_id}_api_sync", source_system=source_id)
    staged = _attach_pipeline_station_sync(request, gapped, source=f"{source_id}_api_sync")
    return _finalize_import(request, staged, staged.get("rows"), source=f"{source_id}_api_sync", upsert_objects=False)


@router.post("/validate")
def validate_imports() -> Dict[str, Any]:
    return validate_all_imports()


@router.post("/import/mock")
def import_mock() -> Dict[str, Any]:
    return import_mock_data()


@router.get("/imports")
def imports() -> List[Dict[str, Any]]:
    return list_import_records()


@router.get("/import-records")
def import_records(limit: int = Query(default=50, ge=1, le=200)) -> Dict[str, Any]:
    return list_version_import_records(limit=limit)


@router.get("/metric-facts/summary")
def metric_facts_summary() -> Dict[str, Any]:
    return metric_fact_summary()


@router.get("/data-gaps/summary")
def data_gaps_summary() -> Dict[str, Any]:
    return data_gap_summary()


@router.get("/import-diagnostics")
def import_diagnostics_endpoint(data_version: str | None = Query(default=None, alias="dataVersion")) -> Dict[str, Any]:
    return import_diagnostics(data_version)


@router.get("/versions/{data_version}/detail")
def version_detail(request: Request, data_version: str) -> Dict[str, Any]:
    user_id = request_user_id(request)
    try:
        detail = get_data_version_detail(data_version, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    detail["permissions"] = {"canRollback": can_rollback(user_id) and bool(detail.get("record", {}).get("canRollback")), "canDelete": True, "rollbackRoleIds": sorted(ROLLBACK_ROLE_IDS)}
    return detail


@router.post("/versions/{data_version}/rollback")
def rollback_version(request: Request, data_version: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    user_id = request_user_id(request)
    require_rollback_permission(user_id)
    try:
        return rollback_data_version(data_version, operator_id=user_id, reason=body.get("reason") or body.get("note"), task_strategy=body.get("task_strategy") or body.get("taskStrategy") or "review")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/versions/{data_version}")
def delete_version(request: Request, data_version: str, confirm: bool = Query(default=False), body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    if not confirm:
        raise HTTPException(status_code=400, detail="删除导入记录需要 confirm=true")
    body = body or {}
    user_id = request_user_id(request)
    try:
        return delete_data_version(data_version, operator_id=user_id, reason=body.get("reason") or body.get("note") or "Demo 阶段删除导入记录。")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/templates")
def report_templates() -> Dict[str, Any]:
    return get_report_templates()


@router.post("/upload/preview")
async def preview_upload(file: UploadFile = File(...), dataset_name: str = Form(default="auto"), source_system: str = Form(default="manual_upload")) -> Dict[str, Any]:
    parsed = await _rows_from_uploaded_file(file)
    try:
        preview = preview_report_dataset(str(dataset_name), rows=parsed.get("rows"), source_system=source_system)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    preview["uploadMeta"] = compact_upload_meta(parsed)
    return preview


@router.post("/upload/confirm")
async def confirm_upload(request: Request, file: UploadFile = File(...), dataset_name: str = Form(default="auto"), source_system: str = Form(default="manual_upload"), auto_create_tasks: bool = Form(default=False)) -> Dict[str, Any]:
    parsed = await _rows_from_uploaded_file(file)
    rows = parsed.get("rows")
    try:
        result = confirm_report_import(str(dataset_name), rows=rows, field_mapping={}, auto_create_tasks=False, source_system=source_system)
        result["uploadMeta"] = compact_upload_meta(parsed)
        objected = _attach_operating_object_sync(request, result, rows, source="upload_file_import")
        facted = _attach_v121_metric_fact_sync(objected, rows, source="upload_file_import", source_system=source_system, parsed=parsed)
        gapped = _attach_v1213_data_gap_sync(facted, rows, source="upload_file_import", source_system=source_system, parsed=parsed)
        staged = _attach_pipeline_station_sync(request, gapped, source="upload_file_import")
        return _finalize_import(request, staged, rows, source="upload_file_import", upsert_objects=False)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/preview")
def preview_report(body: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    dataset_name = body.get("dataset_name") or body.get("datasetName")
    if not dataset_name:
        raise HTTPException(status_code=400, detail="dataset_name is required")
    try:
        return preview_report_dataset(str(dataset_name), rows=body.get("rows"), field_mapping=body.get("field_mapping") or body.get("fieldMapping"), source_system=body.get("source_system") or body.get("sourceSystem"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/import/confirm")
def confirm_import(request: Request, body: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    dataset_name = body.get("dataset_name") or body.get("datasetName")
    if not dataset_name:
        raise HTTPException(status_code=400, detail="dataset_name is required")
    source_system = body.get("source_system") or body.get("sourceSystem")
    try:
        result = confirm_report_import(str(dataset_name), rows=body.get("rows"), field_mapping=body.get("field_mapping") or body.get("fieldMapping"), auto_create_tasks=False, source_system=source_system)
        if isinstance(body.get("reportProfile"), dict):
            result["reportProfile"] = body.get("reportProfile")
        objected = _attach_operating_object_sync(request, result, body.get("rows"), source="confirm_report_import")
        facted = _attach_v121_metric_fact_sync(objected, body.get("rows"), source="confirm_report_import", source_system=source_system)
        gapped = _attach_v1213_data_gap_sync(facted, body.get("rows"), source="confirm_report_import", source_system=source_system)
        staged = _attach_pipeline_station_sync(request, gapped, source="confirm_report_import")
        return _finalize_import(request, staged, body.get("rows"), source="confirm_report_import", upsert_objects=False)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/import/report")
def import_report(request: Request, body: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    dataset_name = body.get("dataset_name") or body.get("datasetName")
    if not dataset_name:
        raise HTTPException(status_code=400, detail="dataset_name is required")
    source_system = body.get("source_system") or body.get("sourceSystem")
    try:
        result = import_report_dataset(str(dataset_name), rows=body.get("rows"), auto_create_tasks=False)
        objected = _attach_operating_object_sync(request, result, body.get("rows"), source="report_import")
        facted = _attach_v121_metric_fact_sync(objected, body.get("rows"), source="report_import", source_system=source_system)
        gapped = _attach_v1213_data_gap_sync(facted, body.get("rows"), source="report_import", source_system=source_system)
        staged = _attach_pipeline_station_sync(request, gapped, source="report_import")
        return _finalize_import(request, staged, body.get("rows"), source="report_import", upsert_objects=False)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/import/mock-alerts")
def import_mock_alerts(request: Request) -> Dict[str, Any]:
    result = _run_dataset_imports_without_legacy_tasks()
    result["v3Summary"] = get_v3_dashboard_summary()
    objected = _attach_operating_object_sync(request, result, result.get("rows"), source="mock_alerts_import")
    facted = _attach_v121_metric_fact_sync(objected, objected.get("rows"), source="mock_alerts_import", source_system="mock_alerts")
    gapped = _attach_v1213_data_gap_sync(facted, facted.get("rows"), source="mock_alerts_import", source_system="mock_alerts")
    staged = _attach_pipeline_station_sync(request, gapped, source="mock_alerts_import")
    return _finalize_import(request, staged, staged.get("rows"), source="mock_alerts_import", upsert_objects=False)


@router.get("/v3-summary")
def v3_summary() -> Dict[str, Any]:
    return get_v3_dashboard_summary()


@router.get("/alerts")
def alerts(active_only: bool = Query(default=True)) -> List[Dict[str, Any]]:
    return list_alerts_for_entity(active_only=active_only)


@router.get("/alerts/events")
def alert_events(active_only: bool = Query(default=True)) -> List[Dict[str, Any]]:
    return list_alert_events(active_only=active_only)


@router.get("/versions")
def versions() -> List[Dict[str, Any]]:
    return list_version_import_records(limit=200).get("records", [])
