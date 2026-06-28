"""Data Hub routes."""

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
from src.services.report_alert_service import get_v3_dashboard_summary, import_report_dataset, latest_data_version, list_alert_events, list_alerts_for_entity, list_data_versions
from src.services.report_schema_service import confirm_report_import, get_report_templates, normalize_rows_with_mapping, preview_report_dataset
from src.services.risk_task_service import generate_risk_tasks_for_signals
from src.services.trend_signal_service import ingest_product_trends
from src.services.v104_import_task_sync_service import attach_v104_import_sync
from src.services.v107_operating_profile_service import attach_v107_operating_profile
from src.services.v108_tag_change_task_service import attach_v108_tag_change_tasks
from src.services.v116_import_closed_loop_service import attach_v116_import_closed_loop

router = APIRouter(prefix="/api/data", tags=["data-import"])
ROLLBACK_ROLE_IDS = {"owner", "manager", "finance"}
DEFAULT_SYNC_DATASETS = ["inventory", "refunds", "orders", "products"]


def request_user_id(request: Request) -> str:
    return user_id_from_headers(request.headers)


def can_rollback(user_id: str) -> bool:
    user = current_user(user_id)
    return user.get("roleId") in ROLLBACK_ROLE_IDS


def require_rollback_permission(user_id: str) -> None:
    if not can_rollback(user_id):
        raise HTTPException(status_code=403, detail="当前账号无权回滚全局数据版本")


def _dataset_rows(dataset_name: str | None) -> List[Dict[str, Any]]:
    name = str(dataset_name or "").strip()
    config = DATASET_CONFIGS.get(name)
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
        result["rule"] = "V12.5：接口/演示同步只写事实和缺口；第一份报表只建基线，任务由红线 + ROI/GMV 对比 + 证据闸门生成。"
        results.append(result)
        all_rows.extend(normalized)
    return {
        "version": "12.5.0",
        "mode": "v12_5_dataset_sync_without_legacy_task_rules",
        "datasetCount": len(results),
        "rowCount": len(all_rows),
        "alertCount": sum(item.get("alertCount", 0) for item in results),
        "createdTaskCount": 0,
        "taggedAlertCount": sum(item.get("taggedAlertCount", 0) for item in results),
        "results": results,
        "rows": all_rows,
        "summary": get_v3_dashboard_summary(),
        "rule": "导入先完成经营对象、指标事实和缺口留痕；首份报表只做基线，后续对比后再生成 ROI/GMV 经营任务。",
    }


def _attach_operating_object_sync(request: Request, result: Dict[str, Any], rows: Any, *, source: str) -> Dict[str, Any]:
    materialized_rows = _materialize_import_rows(result, rows)
    if materialized_rows:
        result["rows"] = materialized_rows
    ctx = context_from_headers(request.headers)
    result["operatingObjectSync"] = upsert_operating_objects_from_import(
        result,
        materialized_rows,
        source=source,
        uploader_user_id=ctx.user_id,
        uploader_role_id=ctx.role_id,
    )
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
        result["metricFactSync"] = ingest_metric_facts_from_sheet_rows(
            result,
            parsed,
            report_profile=_report_profile_from_result(result),
            source_system=source_system or result.get("sourceSystem"),
            source_report_id=source,
        )
        return result
    if not materialized_rows:
        result["metricFactSync"] = {"version": "12.5.0", "skipped": True, "reason": "rows is not a list"}
        return result
    result["metricFactSync"] = ingest_metric_facts_from_import(
        result,
        materialized_rows,
        report_profile=_report_profile_from_result(result),
        source_system=source_system or result.get("sourceSystem"),
        source_report_id=source,
    )
    return result


def _attach_v1213_data_gap_sync(result: Dict[str, Any], rows: Any, *, source: str, source_system: str | None = None, parsed: Dict[str, Any] | None = None) -> Dict[str, Any]:
    materialized_rows = _materialize_import_rows(result, rows)
    if materialized_rows:
        result["rows"] = materialized_rows
    parsed_payload = parsed if isinstance(parsed, dict) else {"rows": materialized_rows}
    result["dataGapSync"] = ingest_data_gaps_from_import(
        result,
        parsed_payload,
        report_profile=_report_profile_from_result(result),
        source_system=source_system or result.get("sourceSystem"),
        source_report_id=source,
    )
    return result


def _attach_import_diagnostics(result: Dict[str, Any]) -> Dict[str, Any]:
    version = result.get("dataVersion")
    if not version and isinstance(result.get("results"), list) and result["results"]:
        version = next((item.get("dataVersion") for item in result["results"] if isinstance(item, dict) and item.get("dataVersion")), None)
    result["importDiagnostics"] = import_diagnostics(
        str(version) if version else None,
        report_profile=_report_profile_from_result(result),
        metric_fact_sync=result.get("metricFactSync") if isinstance(result.get("metricFactSync"), dict) else None,
        data_gap_sync=result.get("dataGapSync") if isinstance(result.get("dataGapSync"), dict) else None,
        risk_task_sync=result.get("riskTaskSync") if isinstance(result.get("riskTaskSync"), dict) else None,
    )
    return result


def _attach_import_product_contracts(request: Request, result: Dict[str, Any], rows: Any, *, source: str, upsert_objects: bool = True) -> Dict[str, Any]:
    if upsert_objects:
        result = _attach_operating_object_sync(request, result, rows, source=source)
        result = _attach_v121_metric_fact_sync(result, rows, source=source)
        result = _attach_v1213_data_gap_sync(result, rows, source=source)
    ctx = context_from_headers(request.headers)
    v104 = attach_v104_import_sync(result, source=source)
    v107 = attach_v107_operating_profile(v104)
    v108 = attach_v108_tag_change_tasks(v107, ctx)
    closed = attach_v116_import_closed_loop(v108, ctx, source=source)
    return _attach_import_diagnostics(closed)


def _attach_v62_trend_and_risk_sync(result: Dict[str, Any], rows: Any, source_system: str | None = None) -> Dict[str, Any]:
    materialized_rows = _materialize_import_rows(result, rows)
    if not materialized_rows:
        result["trendSync"] = {"version": "6.2.0", "skipped": True, "reason": "rows is not a list"}
        result["riskTaskSync"] = {"version": "12.5.0", "skipped": True, "reason": "rows is not a list"}
        return result
    import_results = result.get("results") if isinstance(result.get("results"), list) else [result]
    summaries: List[Dict[str, Any]] = []
    risk_summaries: List[Dict[str, Any]] = []
    for item in import_results:
        if not isinstance(item, dict):
            continue
        dataset_name = item.get("datasetName")
        data_version = item.get("dataVersion")
        if not dataset_name or not data_version:
            continue
        base_rows = item.get("rows") if isinstance(item.get("rows"), list) and item.get("rows") else materialized_rows
        field_mapping = (item.get("schemaPreview") or {}).get("fieldMapping") or {}
        routed_rows = normalize_rows_with_mapping(base_rows, field_mapping) if isinstance(field_mapping, dict) else base_rows
        trend_summary = ingest_product_trends(dataset_name=str(dataset_name), data_version=str(data_version), rows=routed_rows, source_system=source_system or result.get("sourceSystem"))
        risk_summary = generate_risk_tasks_for_signals(data_version=str(data_version))
        item["trendSync"] = trend_summary
        item["riskTaskSync"] = risk_summary
        summaries.append(trend_summary)
        risk_summaries.append(risk_summary)
    result["trendSync"] = {
        "version": "6.2.0",
        "mode": "product_snapshot_metric_trend_signal_sync",
        "datasetCount": len(summaries),
        "snapshotCount": sum(item.get("snapshotCount", 0) for item in summaries),
        "trendCount": sum(item.get("trendCount", 0) for item in summaries),
        "signalCount": sum(item.get("signalCount", 0) for item in summaries),
        "taskCandidateSignalCount": sum(item.get("taskCandidateSignalCount", 0) for item in summaries),
        "summaries": summaries,
        "rule": "导入后先生成商品快照、指标趋势和经营信号。",
    }
    result["riskTaskSync"] = {
        "version": "12.5.0",
        "mode": "v12_5_baseline_first_redline_plus_roi_gmv_operating_task_generation",
        "primaryAxis": "ROI_GMV",
        "datasetCount": len(risk_summaries),
        "createdTaskCount": sum(item.get("createdTaskCount", 0) for item in risk_summaries),
        "strictRiskCreatedTaskCount": sum(item.get("strictRiskCreatedTaskCount", 0) for item in risk_summaries),
        "operatingCadenceCreatedTaskCount": sum(item.get("operatingCadenceCreatedTaskCount", 0) for item in risk_summaries),
        "blockedByBaselineCount": sum(item.get("blockedByBaselineCount", 0) for item in risk_summaries),
        "baselineMode": any(bool(item.get("baselineMode")) for item in risk_summaries),
        "comparisonReady": any(bool(item.get("comparisonReady")) for item in risk_summaries),
        "trendReady": any(bool(item.get("trendReady")) for item in risk_summaries),
        "signalCount": sum(item.get("signalCount", 0) for item in risk_summaries),
        "groupCount": sum(item.get("groupCount", 0) for item in risk_summaries),
        "evidenceBlockedTaskCount": sum((item.get("evidenceGateSync") or {}).get("blockedTaskCount", 0) for item in risk_summaries),
        "summaries": risk_summaries,
        "rule": "V12.5：首份报表只建基线；非红线 ROI/GMV 经营任务必须至少有两份可比报表；关键证据缺失时按 metric_scope 降级为补证任务。",
    }
    return result


async def _rows_from_uploaded_file(file: UploadFile) -> Dict[str, Any]:
    content = await file.read()
    try:
        return parse_upload_file(file.filename or "upload", content, content_type=file.content_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/sources")
def data_sources() -> List[Dict[str, Any]]:
    return list_import_sources()


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
    synced = _attach_v62_trend_and_risk_sync(gapped, gapped.get("rows"), source_system=source_id)
    return _attach_import_product_contracts(request, synced, synced.get("rows"), source=f"{source_id}_api_sync", upsert_objects=False)


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
async def confirm_upload(request: Request, file: UploadFile = File(...), dataset_name: str = Form(default="auto"), source_system: str = Form(default="manual_upload"), auto_create_tasks: bool = Form(default=True)) -> Dict[str, Any]:
    parsed = await _rows_from_uploaded_file(file)
    rows = parsed.get("rows")
    try:
        result = confirm_report_import(str(dataset_name), rows=rows, field_mapping={}, auto_create_tasks=False, source_system=source_system)
        result["uploadMeta"] = compact_upload_meta(parsed)
        objected = _attach_operating_object_sync(request, result, rows, source="upload_file_import")
        facted = _attach_v121_metric_fact_sync(objected, rows, source="upload_file_import", source_system=source_system, parsed=parsed)
        gapped = _attach_v1213_data_gap_sync(facted, rows, source="upload_file_import", source_system=source_system, parsed=parsed)
        synced = _attach_v62_trend_and_risk_sync(gapped, rows, source_system=source_system)
        return _attach_import_product_contracts(request, synced, rows, source="upload_file_import", upsert_objects=False)
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
        synced = _attach_v62_trend_and_risk_sync(gapped, body.get("rows"), source_system=source_system)
        return _attach_import_product_contracts(request, synced, body.get("rows"), source="confirm_report_import", upsert_objects=False)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/import/report")
def import_report(request: Request, body: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    dataset_name = body.get("dataset_name") or body.get("datasetName")
    if not dataset_name:
        raise HTTPException(status_code=400, detail="dataset_name is required")
    try:
        result = import_report_dataset(str(dataset_name), rows=body.get("rows"), auto_create_tasks=False)
        objected = _attach_operating_object_sync(request, result, body.get("rows"), source="report_import")
        facted = _attach_v121_metric_fact_sync(objected, body.get("rows"), source="report_import", source_system=body.get("source_system") or body.get("sourceSystem"))
        gapped = _attach_v1213_data_gap_sync(facted, body.get("rows"), source="report_import", source_system=body.get("source_system") or body.get("sourceSystem"))
        synced = _attach_v62_trend_and_risk_sync(gapped, body.get("rows"), source_system=body.get("source_system") or body.get("sourceSystem"))
        return _attach_import_product_contracts(request, synced, body.get("rows"), source="report_import", upsert_objects=False)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/import/mock-alerts")
def import_mock_alerts(request: Request) -> Dict[str, Any]:
    result = _run_dataset_imports_without_legacy_tasks()
    result["v3Summary"] = get_v3_dashboard_summary()
    objected = _attach_operating_object_sync(request, result, result.get("rows"), source="mock_alerts_import")
    facted = _attach_v121_metric_fact_sync(objected, objected.get("rows"), source="mock_alerts_import", source_system="mock_alerts")
    gapped = _attach_v1213_data_gap_sync(facted, facted.get("rows"), source="mock_alerts_import", source_system="mock_alerts")
    synced = _attach_v62_trend_and_risk_sync(gapped, gapped.get("rows"), source_system="mock_alerts")
    return _attach_import_product_contracts(request, synced, synced.get("rows"), source="mock_alerts_import", upsert_objects=False)


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
    return list_data_versions()


@router.get("/latest-version")
def latest_version_endpoint() -> Dict[str, Any]:
    return latest_data_version()
