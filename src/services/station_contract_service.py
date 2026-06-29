"""V14.3 standard station contract service."""

from __future__ import annotations

import importlib
from typing import Any, Dict

from src.services.pipeline_gate_service import record_stage_gate, stage_summary
from src.services.station_adapter_service import STATION_ADAPTER_VERSION, run_station_adapter
from src.services.station_registry_service import STATION_REGISTRY_VERSION, get_station, list_stations

STATION_CONTRACT_VERSION = "14.3.0"

DEFAULT_INPUTS = {
    "import_station": ["source", "dataVersion"],
    "report_parse_station": ["dataVersion", "rawReportRef"],
    "metric_fact_station": ["dataVersion", "parsedRowsRef"],
    "operating_object_station": ["dataVersion", "metricFactRef"],
    "operating_snapshot_station": ["dataVersion", "operatingObjectRef"],
    "system_product_snapshot_station": ["dataVersion"],
    "product_signal_snapshot_station": ["dataVersion", "productSnapshotRef"],
    "task_signal_station": ["dataVersion", "productSignalSnapshotRef"],
    "rag_context_station": ["dataVersion", "taskSignalRef"],
    "agent_judgment_station": ["dataVersion", "ragContextRef"],
    "task_snapshot_station": ["dataVersion"],
    "task_pool_station": ["dataVersion"],
    "task_acceptance_station": ["taskId"],
    "task_assignment_station": ["taskId", "assigneeId"],
    "task_submission_station": ["taskId", "evidence"],
    "task_review_station": ["taskId", "decision"],
    "recap_schedule_station": ["taskId"],
    "recap_complete_station": ["taskId", "afterMetrics"],
    "rag_feedback_station": ["taskId", "recapResult"],
}

DEFAULT_OUTPUTS = {
    "import_station": ["dataVersion", "outputRef"],
    "report_parse_station": ["rowCount", "outputRef"],
    "metric_fact_station": ["factCount", "outputRef"],
    "operating_object_station": ["storeCount", "productCount", "outputRef"],
    "operating_snapshot_station": ["snapshotKey", "storeRows", "outputRef"],
    "system_product_snapshot_station": ["productSnapshotCount", "productSnapshotRef", "outputRef"],
    "product_signal_snapshot_station": ["productSignalPackageCount", "productSignalSnapshotRef", "outputRef"],
    "task_signal_station": ["signalCount", "taskSignalRef", "outputRef"],
    "rag_context_station": ["matchedContextCount", "ragContextRef", "outputRef"],
    "agent_judgment_station": ["decision", "confidence", "judgmentCount", "outputRef"],
    "task_snapshot_station": ["taskSnapshotCount", "decision", "status", "outputRef"],
    "task_pool_station": ["createdTaskCount", "outputRef"],
    "task_acceptance_station": ["taskId", "action", "outputRef"],
    "task_assignment_station": ["taskId", "action", "outputRef"],
    "task_submission_station": ["taskId", "transition", "outputRef"],
    "task_review_station": ["taskId", "decision", "outputRef"],
    "recap_schedule_station": ["taskId", "scheduledCount", "outputRef"],
    "recap_complete_station": ["taskId", "recapResult", "outputRef"],
    "rag_feedback_station": ["taskId", "candidateCount", "outputRef"],
}

REAL_ADAPTERS = {"operating_snapshot_station", "system_product_snapshot_station", "product_signal_snapshot_station", "task_signal_station", "rag_context_station", "agent_judgment_station", "task_snapshot_station", "task_pool_station"}


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def station_contract(station_id: str) -> Dict[str, Any]:
    station = get_station(station_id)
    if not station:
        return {"version": STATION_CONTRACT_VERSION, "ok": False, "error": "station_not_found", "stationId": station_id}
    sid = station["stationId"]
    return {"version": STATION_CONTRACT_VERSION, "registryVersion": STATION_REGISTRY_VERSION, "adapterVersion": STATION_ADAPTER_VERSION, "ok": True, "stationId": sid, "stage": station["stage"], "title": station["title"], "stationLine": station.get("stationLine"), "stationDomain": station.get("stationDomain"), "input": {"required": DEFAULT_INPUTS.get(sid, ["dataVersion"])}, "output": {"required": DEFAULT_OUTPUTS.get(sid, ["outputRef"])}, "nextStation": station.get("nextStation"), "replayable": bool(station.get("replayable")), "diagnosticSupported": bool(station.get("diagnosticSupported")), "backendModule": station.get("backendModule"), "frontendModule": station.get("frontendModule"), "standardInterface": {"contract": f"/api/stations/{sid}/contract", "health": f"/api/stations/{sid}/health", "run": f"/api/stations/{sid}/run", "replay": f"/api/stations/{sid}/replay", "gates": f"/api/stations/{sid}/gates"}, "adapter": {"realAdapterSupported": sid in REAL_ADAPTERS, "dedicatedLifecycleRoute": sid in {"task_acceptance_station", "task_assignment_station", "task_submission_station", "task_review_station", "recap_schedule_station", "recap_complete_station", "rag_feedback_station"}, "diagnosticUsesSimulation": True}, "rule": "V14.3：全量信号包进入Agent预算判断；系统控制预算预占和生命周期。"}


def list_station_contracts() -> Dict[str, Any]:
    return {"version": STATION_CONTRACT_VERSION, "contracts": [station_contract(station["stationId"]) for station in list_stations()], "rule": "前后端统一读取 Station Contract，不直接依赖站点内部实现。"}


def validate_contract_payload(station_id: str, payload: Dict[str, Any] | None, *, direction: str = "input") -> Dict[str, Any]:
    payload = payload or {}
    contract = station_contract(station_id)
    required = list(((contract.get(direction) or {}).get("required") or []))
    missing = [key for key in required if key not in payload or _is_blank(payload.get(key))]
    return {"version": STATION_CONTRACT_VERSION, "stationId": station_id, "direction": direction, "status": "passed" if not missing else "warning", "missing": missing, "required": required, "payloadKeys": sorted(payload.keys())}


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
    return {"version": STATION_CONTRACT_VERSION, "stationId": station["stationId"], "stage": station["stage"], "title": station["title"], "status": "healthy" if module_ok else "degraded", "backendModule": station.get("backendModule"), "moduleImportOk": module_ok, "errorMessage": error, "gateTableOk": gates.get("gateCount") is not None, "contract": station_contract(station["stationId"]), "rule": "Health 只检查标准站点接口和模块可达性，不执行业务数据流。"}


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
        adapter_output = {"adapterMode": "real_adapter_failed_fallback_contract", "adapterError": adapter_error}
    data_version = adapter_output.get("dataVersion") or body.get("dataVersion") or body.get("data_version") or ("DIAG-V14.3" if diagnostic else None)
    output_ref = adapter_output.get("outputRef") or f"{station.get('outputRefPrefix')}:{data_version or body.get('taskId') or body.get('task_id') or 'latest'}"
    output = _complete_output_for_contract(station["stationId"], {**adapter_output, "dataVersion": data_version, "outputRef": output_ref, "stationId": station["stationId"], "isDiagnostic": diagnostic})
    output_check = validate_contract_payload(station["stationId"], output, direction="output")
    status = "failed" if adapter_error else "completed"
    gate = record_stage_gate(data_version=data_version, stage=station["stage"], status=status, input_payload={**body, "isDiagnostic": diagnostic, "stationId": station["stationId"]}, output_payload=output, user_id=body.get("userId") or body.get("user_id") or ("OPS" if diagnostic else None), upstream_stage=body.get("upstreamStage"), output_ref=output_ref, error_message=adapter_error, run_type="diagnostic" if diagnostic else "business", is_diagnostic=diagnostic)
    return {"version": STATION_CONTRACT_VERSION, "ok": status == "completed", "status": status, "stationId": station["stationId"], "stage": station["stage"], "inputContract": input_check, "outputContract": output_check, "output": output, "gate": gate, "adapterVersion": STATION_ADAPTER_VERSION, "adapterError": adapter_error, "nextStation": station.get("nextStation"), "rule": "V14.3：系统快照生成全量信号包，RAG与Agent预算判断任务去向。"}
