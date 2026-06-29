"""V12.14.1 Pipeline compatibility routes.

Pipeline routes remain for backward compatibility, but they no longer reach into
station internals. They delegate to Station Interface so the main route is
station-contract governed.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, Query, Request

from src.services.account_service import user_id_from_headers
from src.services.pipeline_gate_service import PIPELINE_GATE_VERSION, PIPELINE_STAGES, record_stage_gate, stage_summary
from src.services.station_contract_service import run_station_contract
from src.services.station_registry_service import station_by_stage

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])
PIPELINE_ROUTE_VERSION = "12.14.1"


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
    return {"version": PIPELINE_ROUTE_VERSION, "compatibilityLayer": "station_interface", "stage": "operating_unit_snapshot_ready", "stationRun": result, "snapshot": (result.get("output") or {}).get("adapterResult"), "rule": "旧pipeline快照接口仅转发到 operating_snapshot_station。"}


@router.post("/data-versions/{data_version}/tasks/generate")
def generate_tasks_station(request: Request, data_version: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    payload = _station_body(request, data_version, body)
    payload.setdefault("snapshotRef", f"operating_unit_snapshot:{data_version}")
    payload.setdefault("upstreamStage", "operating_unit_snapshot_ready")
    result = run_station_contract("task_signal_station", payload, diagnostic=False)
    output = result.get("output") or {}
    task_generation = output.get("adapterResult") or {"createdTaskCount": output.get("createdTaskCount", 0), "skipped": True, "reason": "adapter_result_missing"}
    return {"version": PIPELINE_ROUTE_VERSION, "compatibilityLayer": "station_interface", "stationRun": result, "taskGeneration": task_generation, "rule": "旧pipeline任务生成接口已删除直接service调用，只转发到 task_signal_station。"}
