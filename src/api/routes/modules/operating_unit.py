"""Operating unit module route.

V12.13 rule: the operating page is a snapshot reader. It must not re-run report
projection, traffic projection, task generation, RAG retrieval or LLM generation
when the page is opened.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Query, Request

from src.services.account_service import current_user, user_id_from_headers
from src.services.operating_unit_snapshot_service import OPERATING_UNIT_SNAPSHOT_VERSION, get_operating_unit_snapshot, materialize_operating_unit_snapshot
from src.services.pipeline_gate_service import PIPELINE_GATE_VERSION, stage_summary

router = APIRouter()
OPERATING_UNIT_VERSION = "12.13.0"


def _viewer(request: Request) -> tuple[str, Dict[str, Any]]:
    user_id = user_id_from_headers(request.headers)
    return user_id, current_user(user_id)


@router.get("/operating-unit")
def operating_unit(request: Request, data_version: str | None = Query(default=None, alias="dataVersion")) -> Dict[str, Any]:
    user_id, user = _viewer(request)
    snapshot = get_operating_unit_snapshot(user_id=user_id, data_version=data_version, allow_build=True)
    snapshot["version"] = OPERATING_UNIT_VERSION
    snapshot["snapshotVersion"] = OPERATING_UNIT_SNAPSHOT_VERSION
    snapshot["pipelineGateVersion"] = PIPELINE_GATE_VERSION
    snapshot["viewer"] = {"id": user.get("id"), "roleId": user.get("roleId"), "roleName": user.get("roleName")}
    snapshot["readMode"] = "snapshot_only"
    snapshot["forbiddenRuntimeStages"] = ["projected_products", "projected_traffic", "projection_summary", "dataset_rows", "rag_retrieval", "llm_generation"]
    snapshot["rule"] = "V12.13：经营页只读 operating_unit_snapshot。上传、解析、对象映射、任务生成、Agent增强均为独立pipeline站点。"
    return snapshot


@router.post("/operating-unit/snapshot/rebuild")
def rebuild_operating_unit_snapshot(request: Request, data_version: str | None = Query(default=None, alias="dataVersion")) -> Dict[str, Any]:
    user_id, user = _viewer(request)
    snapshot = materialize_operating_unit_snapshot(user_id=user_id, data_version=data_version, force=True)
    snapshot["version"] = OPERATING_UNIT_VERSION
    snapshot["snapshotVersion"] = OPERATING_UNIT_SNAPSHOT_VERSION
    snapshot["pipelineGateVersion"] = PIPELINE_GATE_VERSION
    snapshot["viewer"] = {"id": user.get("id"), "roleId": user.get("roleId"), "roleName": user.get("roleName")}
    snapshot["readMode"] = "snapshot_rebuilt"
    return snapshot


@router.get("/operating-unit/pipeline/stages")
def operating_unit_pipeline_stages(request: Request, data_version: str | None = Query(default=None, alias="dataVersion")) -> Dict[str, Any]:
    user_id, _ = _viewer(request)
    return stage_summary(data_version=data_version, user_id=user_id, limit=80)
