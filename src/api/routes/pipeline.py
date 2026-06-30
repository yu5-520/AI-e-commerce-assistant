"""V14.6.2 Pipeline routes with station queue streaming fast lane."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, Query, Request

from src.services.account_service import user_id_from_headers
from src.services.pipeline_gate_service import PIPELINE_GATE_VERSION, PIPELINE_STAGES, record_stage_gate, stage_summary
from src.services.station_contract_service import run_station_contract
from src.services.station_queue_service import STATION_QUEUE_VERSION, enqueue_task_generation, queue_summary, run_next_station_job
from src.services.station_queue_worker_service import STATION_QUEUE_WORKER_VERSION, run_worker_tick, start_station_queue_worker, stop_station_queue_worker, worker_status
from src.services.station_registry_service import station_by_stage
from src.services.v142_task_mainline_service import DEFAULT_AGENT_BATCH_SIZE, run_v143_task_mainline

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])
PIPELINE_ROUTE_VERSION = "14.6.2"


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
    return {"version": PIPELINE_ROUTE_VERSION, "gateVersion": PIPELINE_GATE_VERSION, "queueVersion": STATION_QUEUE_VERSION, "workerVersion": STATION_QUEUE_WORKER_VERSION, "compatibilityLayer": "streaming_fast_lane_queue_runtime", **stage_summary(data_version=data_version, user_id=request_user_id(request), limit=120, include_diagnostic=include_diagnostic)}


@router.get("/queue")
def station_queue_status(data_version: str | None = Query(default=None, alias="dataVersion"), limit: int = Query(default=50, ge=1, le=200), include_worker: bool = Query(default=True, alias="includeWorker")) -> Dict[str, Any]:
    summary = queue_summary(data_version=data_version, limit=limit)
    if include_worker:
        summary["worker"] = worker_status(include_queue=False)
    return summary


@router.get("/queue/worker")
def queue_worker_status() -> Dict[str, Any]:
    return worker_status(include_queue=True)


@router.post("/queue/worker/start")
def queue_worker_start(body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    return start_station_queue_worker(worker_id=body.get("workerId") or "api-auto-worker")


@router.post("/queue/worker/stop")
def queue_worker_stop() -> Dict[str, Any]:
    return stop_station_queue_worker()


@router.post("/queue/worker/tick")
def queue_worker_tick(body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    return run_worker_tick(worker_id=body.get("workerId") or "api-manual-tick", limit=body.get("limit"))


@router.post("/queue/run-next")
def run_next_queue_station(body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    return run_next_station_job(worker_id=body.get("workerId") or "api-worker", system_type=body.get("systemType") or "task_generation")


@router.post("/queue/run-batch")
def run_queue_batch(body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    limit = max(1, min(int(body.get("limit") or 1), 20))
    results = [run_next_station_job(worker_id=body.get("workerId") or "api-worker", system_type=body.get("systemType") or "task_generation") for _ in range(limit)]
    return {"version": PIPELINE_ROUTE_VERSION, "queueVersion": STATION_QUEUE_VERSION, "workerVersion": STATION_QUEUE_WORKER_VERSION, "requested": limit, "ranCount": sum(1 for item in results if item.get("ran")), "results": results, "rule": "V14.6.2 prioritizes task_pool and task_snapshot fast lane before lower-priority generation work."}


@router.post("/data-versions/{data_version}/task-generation/enqueue")
def enqueue_task_generation_route(request: Request, data_version: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    return enqueue_task_generation(data_version, actor_user_id=request_user_id(request), input_ref=body.get("inputRef") or f"operating_unit_snapshot:{data_version}", source=body.get("source") or "manual_enqueue", force=bool(body.get("force", True)))


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


@router.post("/data-versions/{data_version}/tasks/generate")
def generate_tasks_station(request: Request, data_version: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    if body.get("sync") is True:
        max_signals = int(body.get("maxSignals") or body.get("agentBatchSize") or DEFAULT_AGENT_BATCH_SIZE)
        return run_v143_task_mainline(data_version, user_id=request_user_id(request), max_signals=max_signals, force=bool(body.get("force", True)), source=body.get("source") or "pipeline_route_sync_legacy")
    return enqueue_task_generation(data_version, actor_user_id=request_user_id(request), input_ref=body.get("inputRef") or f"operating_unit_snapshot:{data_version}", source=body.get("source") or "pipeline_route_queue", force=bool(body.get("force", True)))
