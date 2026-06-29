"""V12.13 pipeline station routes.

These routes expose the station/gate model. Page modules read snapshots; pipeline
routes materialize station outputs explicitly.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, Query, Request

from src.services.account_service import user_id_from_headers
from src.services.operating_unit_snapshot_service import materialize_operating_unit_snapshot
from src.services.pipeline_gate_service import PIPELINE_GATE_VERSION, PIPELINE_STAGES, record_stage_gate, stage_summary
from src.services.risk_task_service import generate_risk_tasks_for_signals

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])
PIPELINE_ROUTE_VERSION = "12.13.0"


def request_user_id(request: Request) -> str:
    return user_id_from_headers(request.headers)


@router.get("/stages")
def pipeline_stages(request: Request, data_version: str | None = Query(default=None, alias="dataVersion")) -> Dict[str, Any]:
    return {"version": PIPELINE_ROUTE_VERSION, "gateVersion": PIPELINE_GATE_VERSION, **stage_summary(data_version=data_version, user_id=request_user_id(request), limit=120)}


@router.post("/data-versions/{data_version}/stage/{stage}/complete")
def complete_stage(request: Request, data_version: str, stage: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    gate = record_stage_gate(data_version=data_version, stage=stage, status=body.get("status") or "completed", input_payload=body.get("input") or {}, output_payload=body.get("output") or body, user_id=request_user_id(request), upstream_stage=body.get("upstreamStage"), output_ref=body.get("outputRef"), error_message=body.get("errorMessage"))
    return {"version": PIPELINE_ROUTE_VERSION, "gate": gate, "knownStages": PIPELINE_STAGES}


@router.post("/data-versions/{data_version}/operating-unit-snapshot")
def build_operating_unit_snapshot(request: Request, data_version: str, force: bool = Query(default=False)) -> Dict[str, Any]:
    snapshot = materialize_operating_unit_snapshot(user_id=request_user_id(request), data_version=data_version, force=force)
    return {"version": PIPELINE_ROUTE_VERSION, "stage": "operating_unit_snapshot_ready", "snapshot": snapshot, "rule": "经营页后续只读取该快照，不重复触发上游流程。"}


@router.post("/data-versions/{data_version}/tasks/generate")
def generate_tasks_station(request: Request, data_version: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    """Explicit task-generation station.

    This endpoint is intentionally not called by operating-unit pages. It can be
    triggered by import completion or manually in demo to create tasks once for a
    data_version.
    """
    body = body or {}
    user_id = request_user_id(request)
    start_gate = record_stage_gate(data_version=data_version, stage="task_signal_ready", status="running", input_payload={"dataVersion": data_version, "requestedBy": user_id, "body": body}, user_id=user_id, upstream_stage="operating_unit_snapshot_ready")
    result = generate_risk_tasks_for_signals(data_version=data_version, requester_role_id=body.get("requesterRoleId") or "operator")
    finish_gate = record_stage_gate(data_version=data_version, stage="task_signal_ready", status="completed", input_payload={"dataVersion": data_version, "requestedBy": user_id}, output_payload={"createdTaskCount": result.get("createdTaskCount"), "strictRiskCreatedTaskCount": result.get("strictRiskCreatedTaskCount"), "operatingCadenceCreatedTaskCount": result.get("operatingCadenceCreatedTaskCount")}, user_id=user_id, upstream_stage="operating_unit_snapshot_ready", output_ref=f"tasks:{data_version}")
    return {"version": PIPELINE_ROUTE_VERSION, "startGate": start_gate, "finishGate": finish_gate, "taskGeneration": result, "rule": "任务生成是独立pipeline站点；页面刷新不触发任务生成。"}
