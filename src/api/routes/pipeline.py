"""V14 Pipeline compatibility routes.

Pipeline routes remain for backward compatibility. V14 keeps the public route but
runs the standard station chain: operating snapshot -> signal pool -> RAG context
-> Agent judgment -> task snapshot -> task pool.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, Query, Request

from src.services.account_service import user_id_from_headers
from src.services.pipeline_gate_service import PIPELINE_GATE_VERSION, PIPELINE_STAGES, record_stage_gate, stage_summary
from src.services.station_contract_service import run_station_contract
from src.services.station_registry_service import station_by_stage

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])
PIPELINE_ROUTE_VERSION = "14.0.0"


def request_user_id(request: Request) -> str:
    return user_id_from_headers(request.headers)


def _station_body(request: Request, data_version: str, body: Dict[str, Any] | None = None) -> Dict[str, Any]:
    payload = dict(body or {})
    payload.setdefault("dataVersion", data_version)
    payload.setdefault("userId", request_user_id(request))
    payload.setdefault("useRealAdapter", True)
    return payload


@router.get("/stages")
def pipeline_stages(request: Request, data_version: str | None = Query(default=None, alias="dataVersion"), include_diagnostic: bool = Query(default=False, alias="includeDiagnostic")) -> Dict[str, Any]:
    return {"version": PIPELINE_ROUTE_VERSION, "gateVersion": PIPELINE_GATE_VERSION, "compatibilityLayer": "station_interface", **stage_summary(data_version=data_version, user_id=request_user_id(request), limit=120, include_diagnostic=include_diagnostic)}


@router.post("/data-versions/{data_version}/stage/{stage}/complete")
def complete_stage(request: Request, data_version: str, stage: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    station = station_by_stage(stage)
    if station:
        result = run_station_contract(station["stationId"], _station_body(request, data_version, {**body, "upstreamStage": body.get("upstreamStage"), "useRealAdapter": False}), diagnostic=bool(body.get("isDiagnostic")))
        return {"version": PIPELINE_ROUTE_VERSION, "compatibilityLayer": "station_interface", "stationRun": result, "knownStages": PIPELINE_STAGES}
    gate = record_stage_gate(data_version=data_version, stage=stage, status=body.get("status") or "completed", input_payload=body.get("input") or {}, output_payload=body.get("output") or body, user_id=request_user_id(request), upstream_stage=body.get("upstreamStage"), output_ref=body.get("outputRef"), error_message=body.get("errorMessage"), run_type="diagnostic" if body.get("isDiagnostic") else "business", is_diagnostic=bool(body.get("isDiagnostic")))
    return {"version": PIPELINE_ROUTE_VERSION, "compatibilityLayer": "manual_gate_only", "gate": gate, "knownStages": PIPELINE_STAGES}


@router.post("/data-versions/{data_version}/operating-unit-snapshot")
def build_operating_unit_snapshot(request: Request, data_version: str, force: bool = Query(default=False), body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    payload = _station_body(request, data_version, body)
    payload.setdefault("operatingObjectRef", f"operating_objects:{data_version}")
    payload["force"] = force
    result = run_station_contract("operating_snapshot_station", payload, diagnostic=False)
    return {"version": PIPELINE_ROUTE_VERSION, "compatibilityLayer": "station_interface", "stage": "operating_unit_snapshot_ready", "stationRun": result, "snapshot": (result.get("output") or {}).get("snapshot"), "rule": "pipeline快照接口转发到 operating_snapshot_station。"}


def _chain_step(station_id: str, request: Request, data_version: str, body: Dict[str, Any], upstream_stage: str | None = None) -> Dict[str, Any]:
    payload = _station_body(request, data_version, body)
    if upstream_stage:
        payload.setdefault("upstreamStage", upstream_stage)
    return run_station_contract(station_id, payload, diagnostic=False)


@router.post("/data-versions/{data_version}/tasks/generate")
def generate_tasks_station(request: Request, data_version: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    max_signals = int(body.get("maxSignals") or 32)

    snapshot = _chain_step(
        "operating_snapshot_station",
        request,
        data_version,
        {**body, "operatingObjectRef": f"operating_objects:{data_version}", "force": body.get("force", True)},
        "operating_objects_ready",
    )
    signal = _chain_step(
        "task_signal_station",
        request,
        data_version,
        {**body, "snapshotRef": (snapshot.get("output") or {}).get("outputRef") or f"operating_unit_snapshot:{data_version}", "maxSignals": max_signals},
        "operating_unit_snapshot_ready",
    )
    signal_output = signal.get("output") or {}
    rag = _chain_step(
        "rag_context_station",
        request,
        data_version,
        {**body, "taskSignalRef": signal_output.get("taskSignalRef") or signal_output.get("outputRef"), "limit": max_signals},
        "task_signal_ready",
    )
    rag_output = rag.get("output") or {}
    agent = _chain_step(
        "agent_judgment_station",
        request,
        data_version,
        {**body, "ragContextRef": rag_output.get("ragContextRef") or rag_output.get("outputRef"), "maxSignals": max_signals},
        "rag_context_ready",
    )
    task_snapshot = _chain_step(
        "task_snapshot_station",
        request,
        data_version,
        {**body, "limit": max_signals},
        "agent_judgment_ready",
    )
    pool = _chain_step(
        "task_pool_station",
        request,
        data_version,
        {**body, "limit": max_signals},
        "task_snapshot_ready",
    )

    outputs = {
        "operatingSnapshot": snapshot.get("output") or {},
        "signalPool": signal_output,
        "ragContext": rag_output,
        "agentJudgment": agent.get("output") or {},
        "taskSnapshot": task_snapshot.get("output") or {},
        "taskPool": pool.get("output") or {},
    }
    created_count = int((outputs["taskPool"].get("createdTaskCount") or 0))
    signal_count = int(outputs["signalPool"].get("signalCount") or 0)
    judgment_count = int(outputs["agentJudgment"].get("judgmentCount") or 0)
    snapshot_count = int(outputs["taskSnapshot"].get("taskSnapshotCount") or 0)
    return {
        "version": PIPELINE_ROUTE_VERSION,
        "compatibilityLayer": "v14_full_station_mainline",
        "dataVersion": data_version,
        "stationRuns": {
            "operatingSnapshot": snapshot,
            "signal": signal,
            "rag": rag,
            "agent": agent,
            "taskSnapshot": task_snapshot,
            "taskPool": pool,
        },
        "taskGeneration": {
            "version": PIPELINE_ROUTE_VERSION,
            "mode": "signal_rag_agent_snapshot_pool",
            "signalCount": signal_count,
            "judgmentCount": judgment_count,
            "taskSnapshotCount": snapshot_count,
            "createdTaskCount": created_count,
            "observeOrNoiseCount": max(judgment_count - snapshot_count, 0),
            "outputs": outputs,
        },
        "rule": "V14：旧任务生成接口保留，但内部改为完整站点链路，不再由任务信号站直接创建任务。",
    }
