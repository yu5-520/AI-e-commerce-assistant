"""V12.14.1 standard station contract service.

Station Interface is the only stable surface for pipeline station execution. Old
pipeline routes must call this layer instead of reaching into service internals.
Diagnostic runs stay simulated; business runs may use station adapters.
"""

from __future__ import annotations

import importlib
from typing import Any, Dict

from src.services.pipeline_gate_service import record_stage_gate, stage_summary
from src.services.station_registry_service import STATION_REGISTRY_VERSION, get_station, list_stations

STATION_CONTRACT_VERSION = "12.14.1"

DEFAULT_INPUTS = {
    "import_station": ["source", "dataVersion"],
    "report_parse_station": ["dataVersion", "rawReportRef"],
    "metric_fact_station": ["dataVersion", "parsedRowsRef"],
    "operating_object_station": ["dataVersion", "metricFactRef"],
    "operating_snapshot_station": ["dataVersion", "operatingObjectRef"],
    "task_signal_station": ["dataVersion", "snapshotRef"],
    "agent_enhance_station": ["dataVersion", "taskSignalRef"],
    "evidence_station": ["taskId", "submitterId"],
    "auto_recap_station": ["taskId", "evidenceRef"],
    "rag_feedback_station": ["recapRef", "reviewStatus"],
}

DEFAULT_OUTPUTS = {
    "import_station": ["dataVersion", "outputRef"],
    "report_parse_station": ["rowCount", "outputRef"],
    "metric_fact_station": ["factCount", "outputRef"],
    "operating_object_station": ["storeCount", "productCount", "outputRef"],
    "operating_snapshot_station": ["snapshotKey", "storeRows", "outputRef"],
    "task_signal_station": ["createdTaskCount", "outputRef"],
    "agent_enhance_station": ["enhancedTaskCount", "outputRef"],
    "evidence_station": ["evidenceId", "outputRef"],
    "auto_recap_station": ["recapId", "outputRef"],
    "rag_feedback_station": ["candidateCount", "outputRef"],
}


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value or "0")))
    except Exception:
        return default


def station_contract(station_id: str) -> Dict[str, Any]:
    station = get_station(station_id)
    if not station:
        return {"version": STATION_CONTRACT_VERSION, "ok": False, "error": "station_not_found", "stationId": station_id}
    sid = station["stationId"]
    return {
        "version": STATION_CONTRACT_VERSION,
        "registryVersion": STATION_REGISTRY_VERSION,
        "ok": True,
        "stationId": sid,
        "stage": station["stage"],
        "title": station["title"],
        "input": {"required": DEFAULT_INPUTS.get(sid, ["dataVersion"])},
        "output": {"required": DEFAULT_OUTPUTS.get(sid, ["outputRef"])},
        "nextStation": station.get("nextStation"),
        "replayable": bool(station.get("replayable")),
        "diagnosticSupported": bool(station.get("diagnosticSupported")),
        "backendModule": station.get("backendModule"),
        "frontendModule": station.get("frontendModule"),
        "standardInterface": {"contract": f"/api/stations/{sid}/contract", "health": f"/api/stations/{sid}/health", "run": f"/api/stations/{sid}/run", "replay": f"/api/stations/{sid}/replay", "gates": f"/api/stations/{sid}/gates"},
        "adapter": {"realAdapterSupported": sid in {"operating_snapshot_station", "task_signal_station"}, "diagnosticUsesSimulation": True},
        "rule": "站点只暴露标准契约和标准接口，内部实现可单独维修；旧Pipeline只能作为兼容层调用本站接口。",
    }


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


def _base_output(station: Dict[str, Any], data_version: str | None, diagnostic: bool) -> Dict[str, Any]:
    output_ref = f"{station.get('outputRefPrefix')}:{data_version or 'latest'}"
    output = {"dataVersion": data_version, "outputRef": output_ref, "stationId": station["stationId"], "isDiagnostic": diagnostic, "adapterMode": "simulated"}
    for key in DEFAULT_OUTPUTS.get(station["stationId"], []):
        output.setdefault(key, output_ref if key.endswith("Ref") or key == "outputRef" else 1)
    return output


def _run_real_adapter(station: Dict[str, Any], body: Dict[str, Any], data_version: str | None, output: Dict[str, Any]) -> Dict[str, Any]:
    sid = station["stationId"]
    if sid == "operating_snapshot_station":
        from src.services.operating_unit_snapshot_service import materialize_operating_unit_snapshot

        snapshot = materialize_operating_unit_snapshot(user_id=body.get("userId") or body.get("user_id"), data_version=data_version, force=bool(body.get("force", True)))
        output.update({
            "adapterMode": "real_operating_snapshot_adapter",
            "snapshotKey": snapshot.get("snapshotKey") or output.get("outputRef"),
            "storeRows": len(snapshot.get("storeRows") or []),
            "outputRef": snapshot.get("snapshotKey") or output.get("outputRef"),
            "adapterResult": {"snapshotKey": snapshot.get("snapshotKey"), "hasData": snapshot.get("hasData"), "storeRows": len(snapshot.get("storeRows") or [])},
        })
        return output
    if sid == "task_signal_station":
        from src.services.risk_task_service import generate_risk_tasks_for_signals

        result = generate_risk_tasks_for_signals(data_version=data_version, requester_role_id=body.get("requesterRoleId") or body.get("requester_role_id") or "operator")
        output.update({
            "adapterMode": "real_task_signal_adapter",
            "createdTaskCount": _as_int(result.get("createdTaskCount")),
            "strictRiskCreatedTaskCount": _as_int(result.get("strictRiskCreatedTaskCount")),
            "operatingCadenceCreatedTaskCount": _as_int(result.get("operatingCadenceCreatedTaskCount")),
            "outputRef": f"tasks:{data_version or 'latest'}",
            "adapterResult": result,
        })
        return output
    output["adapterMode"] = "contract_only_no_real_adapter"
    return output


def run_station_contract(station_id: str, body: Dict[str, Any] | None = None, *, diagnostic: bool = False) -> Dict[str, Any]:
    station = get_station(station_id)
    body = body or {}
    if not station:
        return {"version": STATION_CONTRACT_VERSION, "ok": False, "status": "failed", "error": "station_not_found", "stationId": station_id}
    input_check = validate_contract_payload(station["stationId"], body, direction="input")
    data_version = body.get("dataVersion") or body.get("data_version") or ("DIAG-V12-14" if diagnostic else None)
    output = _base_output(station, data_version, diagnostic)
    use_real_adapter = bool(body.get("useRealAdapter", True)) and not diagnostic
    adapter_error = None
    if use_real_adapter:
        try:
            output = _run_real_adapter(station, body, data_version, output)
        except Exception as exc:
            adapter_error = str(exc)
            output["adapterMode"] = "real_adapter_failed_fallback_contract"
            output["adapterError"] = adapter_error
    output_check = validate_contract_payload(station["stationId"], output, direction="output")
    status = "completed" if input_check["status"] != "failed" and output_check["status"] != "failed" and not adapter_error else "failed" if adapter_error else "completed"
    gate = record_stage_gate(data_version=data_version, stage=station["stage"], status=status, input_payload={**body, "isDiagnostic": diagnostic, "stationId": station["stationId"], "useRealAdapter": use_real_adapter}, output_payload=output, user_id=body.get("userId") or body.get("user_id") or ("OPS" if diagnostic else None), upstream_stage=body.get("upstreamStage"), output_ref=output.get("outputRef"), error_message=adapter_error, run_type="diagnostic" if diagnostic else "business", is_diagnostic=diagnostic)
    return {"version": STATION_CONTRACT_VERSION, "ok": status == "completed", "status": status, "stationId": station["stationId"], "stage": station["stage"], "inputContract": input_check, "outputContract": output_check, "output": output, "gate": gate, "nextStation": station.get("nextStation"), "adapterError": adapter_error, "rule": "V12.14.1：站点运行只走 Station Interface；诊断使用模拟，业务可走真实adapter。"}
