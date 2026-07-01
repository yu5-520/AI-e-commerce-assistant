"""V16.5 split station contract service."""

from __future__ import annotations

import importlib
from typing import Any, Dict

from src.services.pipeline_gate_service import record_stage_gate, stage_summary
from src.services.station_adapter_service import STATION_ADAPTER_VERSION, run_station_adapter
from src.services.station_registry_service import STATION_REGISTRY_VERSION, get_station, list_stations

STATION_CONTRACT_VERSION = "16.5"

DEFAULT_INPUTS = {
    "report_receive_station": ["dataVersion"],
    "report_schema_station": ["dataVersion", "rawReportRef"],
    "report_fact_station": ["dataVersion", "reportSchemaMappingRef"],
    "product_master_station": ["dataVersion", "factRef"],
    "product_metric_snapshot_station": ["dataVersion", "productMasterRef"],
    "full_product_bundle_station": ["dataVersion", "productMetricSnapshotRef"],
    "bundle_validation_station": ["dataVersion", "fullProductBundleRef"],
    "product_judgment_agent_station": ["dataVersion", "validatedBundleRef"],
    "product_judgment_package_station": ["dataVersion", "agentJudgmentRef"],
    "rag_permission_context_station": ["dataVersion", "productJudgmentPackageRef"],
    "task_mapping_agent_station": ["dataVersion", "ragPermissionContextRef"],
    "task_pool_admission_station": ["dataVersion", "taskGenerationDecisionRef"],
    "frontend_read_model_station": ["dataVersion", "taskPoolRef"],
    "task_pool_acceptance_station": ["dataVersion", "frontendReadModelRef"],
    "task_acceptance_station": ["taskId"],
    "task_assignment_station": ["taskId", "assigneeId"],
    "task_submission_station": ["taskId", "evidence"],
    "task_review_station": ["taskId", "decision"],
    "recap_schedule_station": ["taskId"],
    "recap_complete_station": ["taskId", "afterMetrics"],
    "rag_feedback_station": ["taskId", "recapResult"],
}

DEFAULT_OUTPUTS = {
    "report_receive_station": ["dataVersion", "rowCount", "rawReportRef", "outputRef"],
    "report_schema_station": ["headerCount", "dateFields", "reportSchemaMappingRef", "outputRef"],
    "report_fact_station": ["productFactCount", "trafficSourceFactCount", "factNamespaceStatus", "factRef", "outputRef"],
    "product_master_station": ["productMasterCount", "productMasterRef", "outputRef"],
    "product_metric_snapshot_station": ["productMetricSnapshotCount", "productMetricSnapshotRef", "outputRef"],
    "full_product_bundle_station": ["productSignalPackageCount", "fullProductBundleRef", "outputRef"],
    "bundle_validation_station": ["bundleCount", "validationStatus", "validatedBundleRef", "outputRef"],
    "product_judgment_agent_station": ["inputBundleCount", "agentJudgmentCount", "coverageRate", "coverageStatus", "agentJudgmentRef", "outputRef"],
    "product_judgment_package_station": ["productJudgmentPackageCount", "candidatePackageCount", "coverageRate", "coverageStatus", "productJudgmentPackageRef", "outputRef"],
    "rag_permission_context_station": ["matchedContextCount", "ragContextRef", "outputRef"],
    "task_mapping_agent_station": ["candidatePackageCount", "taskDecisionCount", "taskGenerationDecisionRef", "outputRef"],
    "task_pool_admission_station": ["taskDecisionCount", "createdTaskCount", "taskPoolRef", "outputRef"],
    "frontend_read_model_station": ["frontendReadModelStatus", "frontendReadModelRef", "outputRef"],
    "task_pool_acceptance_station": ["acceptanceStatus", "mismatchCount", "taskPoolAcceptanceRef", "outputRef"],
    "task_acceptance_station": ["taskId", "action", "outputRef"],
    "task_assignment_station": ["taskId", "action", "outputRef"],
    "task_submission_station": ["taskId", "transition", "outputRef"],
    "task_review_station": ["taskId", "decision", "outputRef"],
    "recap_schedule_station": ["taskId", "scheduledCount", "outputRef"],
    "recap_complete_station": ["taskId", "recapResult", "outputRef"],
    "rag_feedback_station": ["taskId", "candidateCount", "outputRef"],
}

REAL_ADAPTERS = set(DEFAULT_OUTPUTS.keys())


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def station_contract(station_id: str) -> Dict[str, Any]:
    station = get_station(station_id)
    if not station:
        return {"version": STATION_CONTRACT_VERSION, "ok": False, "error": "station_not_found", "stationId": station_id}
    sid = station["stationId"]
    return {"version": STATION_CONTRACT_VERSION, "registryVersion": STATION_REGISTRY_VERSION, "adapterVersion": STATION_ADAPTER_VERSION, "ok": True, "stationId": sid, "requestedStationId": station_id, "stage": station["stage"], "title": station["title"], "stationLine": station.get("stationLine"), "stationDomain": station.get("stationDomain"), "acceptance": station.get("acceptance"), "input": {"required": DEFAULT_INPUTS.get(sid, ["dataVersion"])}, "output": {"required": DEFAULT_OUTPUTS.get(sid, ["outputRef"])}, "nextStation": station.get("nextStation"), "replayable": bool(station.get("replayable")), "diagnosticSupported": bool(station.get("diagnosticSupported")), "backendModule": station.get("backendModule"), "frontendModule": station.get("frontendModule"), "standardInterface": {"contract": f"/api/stations/{sid}/contract", "health": f"/api/stations/{sid}/health", "run": f"/api/stations/{sid}/run", "replay": f"/api/stations/{sid}/replay", "gates": f"/api/stations/{sid}/gates"}, "adapter": {"realAdapterSupported": sid in REAL_ADAPTERS, "diagnosticUsesSimulation": True}, "rule": "V16.5：一个站点只允许一个核心职责；Agent站不入池，系统站负责合包、入池、读模型和验收。"}


def list_station_contracts() -> Dict[str, Any]:
    return {"version": STATION_CONTRACT_VERSION, "contracts": [station_contract(station["stationId"]) for station in list_stations()], "rule": "V16.5 Station Contract 是前后端、队列和适配器的统一接口契约。"}


def validate_contract_payload(station_id: str, payload: Dict[str, Any] | None, *, direction: str = "input") -> Dict[str, Any]:
    payload = payload or {}
    contract = station_contract(station_id)
    required = list(((contract.get(direction) or {}).get("required") or []))
    if direction == "input" and "dataVersion" in required and payload.get("allowMissingDataVersion"):
        required = [item for item in required if item != "dataVersion"]
    missing = [key for key in required if key not in payload or _is_blank(payload.get(key))]
    return {"version": STATION_CONTRACT_VERSION, "stationId": contract.get("stationId") or station_id, "direction": direction, "status": "passed" if not missing else "warning", "missing": missing, "required": required, "payloadKeys": sorted(payload.keys())}


def station_health(station_id: str) -> Dict[str, Any]:
    station = get_station(station_id)
    if not station:
        return {"version": STATION_CONTRACT_VERSION, "stationId": station_id, "status": "failed", "message": "station not found"}
    module_ok = False
    error = None
    try:
        importlib.import_module(str(station.get("backendModule")))
        module_ok = True
    except Exception as exc:
        error = str(exc)
    gates = stage_summary(None, limit=20)
    return {"version": STATION_CONTRACT_VERSION, "stationId": station["stationId"], "stage": station["stage"], "title": station["title"], "status": "healthy" if module_ok else "degraded", "backendModule": station.get("backendModule"), "moduleImportOk": module_ok, "errorMessage": error, "gateTableOk": gates.get("gateCount") is not None, "contract": station_contract(station["stationId"]), "rule": "V16.5 Health checks station module reachability and contract only; it does not run business data."}


def station_gates(station_id: str, data_version: str | None = None, limit: int = 40, *, include_diagnostic: bool = False) -> Dict[str, Any]:
    station = get_station(station_id)
    if not station:
        return {"version": STATION_CONTRACT_VERSION, "stationId": station_id, "gates": [], "error": "station_not_found"}
    summary = stage_summary(data_version=data_version, limit=limit, include_diagnostic=include_diagnostic)
    gates = [gate for gate in summary.get("gates", []) if gate.get("stage") == station["stage"]]
    return {"version": STATION_CONTRACT_VERSION, "stationId": station["stationId"], "stage": station["stage"], "includeDiagnostic": include_diagnostic, "gates": gates, "gateCount": len(gates)}


def _complete_output_for_contract(station_id: str, output: Dict[str, Any]) -> Dict[str, Any]:
    completed = dict(output or {})
    for key in DEFAULT_OUTPUTS.get(station_id, []):
        if key not in completed or _is_blank(completed.get(key)):
            completed[key] = completed.get("outputRef") or completed.get("taskId") or 0
    return completed


def run_station_contract(station_id: str, body: Dict[str, Any] | None = None, *, diagnostic: bool = False) -> Dict[str, Any]:
    station = get_station(station_id)
    body = body or {}
    if not station:
        return {"version": STATION_CONTRACT_VERSION, "ok": False, "status": "failed", "error": "station_not_found", "stationId": station_id}
    input_check = validate_contract_payload(station["stationId"], body, direction="input")
    adapter_error = None
    try:
        adapter_output = run_station_adapter(station, body, diagnostic=diagnostic)
    except Exception as exc:
        adapter_error = str(exc)
        adapter_output = {"adapterMode": "real_adapter_failed_contract_visible", "adapterError": adapter_error}
    data_version = adapter_output.get("dataVersion") or body.get("dataVersion") or body.get("data_version") or ("DIAG-V16.5" if diagnostic else None)
    output_ref = adapter_output.get("outputRef") or f"{station.get('outputRefPrefix')}:{data_version or body.get('taskId') or body.get('task_id') or 'latest'}"
    output = _complete_output_for_contract(station["stationId"], {**adapter_output, "dataVersion": data_version, "outputRef": output_ref, "stationId": station["stationId"], "isDiagnostic": diagnostic})
    output_check = validate_contract_payload(station["stationId"], output, direction="output")
    status = "failed" if adapter_error else "completed"
    gate = record_stage_gate(data_version=data_version, stage=station["stage"], status=status, input_payload={**body, "isDiagnostic": diagnostic, "stationId": station["stationId"]}, output_payload=output, user_id=body.get("userId") or body.get("user_id") or ("OPS" if diagnostic else None), upstream_stage=body.get("upstreamStage"), output_ref=output_ref, error_message=adapter_error, run_type="diagnostic" if diagnostic else "business", is_diagnostic=diagnostic)
    return {"version": STATION_CONTRACT_VERSION, "ok": status == "completed", "status": status, "stationId": station["stationId"], "requestedStationId": station_id, "stage": station["stage"], "inputContract": input_check, "outputContract": output_check, "output": output, "gate": gate, "adapterVersion": STATION_ADAPTER_VERSION, "adapterError": adapter_error, "nextStation": station.get("nextStation"), "rule": "V16.5：Station Contract records every split station boundary; failures are visible and no station silently performs another station's work."}
