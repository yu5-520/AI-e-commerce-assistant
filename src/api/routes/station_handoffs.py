"""V13.1 Station Handoff routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, Query, Request

from src.services.account_service import user_id_from_headers
from src.services.snapshot_task_handoff_service import create_snapshot_task_handoff, handoff_summary, latest_station_handoff, list_station_handoffs

router = APIRouter(prefix="/api/station-handoffs", tags=["station-handoffs"])
STATION_HANDOFF_ROUTE_VERSION = "13.1.0"


def request_user_id(request: Request) -> str:
    return user_id_from_headers(request.headers)


@router.get("")
def station_handoffs(dataVersion: str | None = Query(default=None), limit: int = Query(default=50, ge=1, le=200)) -> Dict[str, Any]:
    result = list_station_handoffs(data_version=dataVersion, limit=limit)
    result["routeVersion"] = STATION_HANDOFF_ROUTE_VERSION
    return result


@router.get("/summary")
def station_handoff_summary(limit: int = Query(default=40, ge=1, le=200)) -> Dict[str, Any]:
    result = handoff_summary(limit=limit)
    result["routeVersion"] = STATION_HANDOFF_ROUTE_VERSION
    return result


@router.get("/latest")
def station_handoff_latest(dataVersion: str | None = Query(default=None)) -> Dict[str, Any]:
    result = latest_station_handoff(data_version=dataVersion)
    result["routeVersion"] = STATION_HANDOFF_ROUTE_VERSION
    return result


@router.post("/snapshot-task")
def snapshot_task_handoff(request: Request, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    result = create_snapshot_task_handoff(
        data_version=body.get("dataVersion") or body.get("data_version"),
        snapshot_ref=body.get("snapshotRef") or body.get("snapshot_ref"),
        source=body.get("source") or "manual_station_handoff",
        user_id=request_user_id(request),
        import_result=body.get("importResult") if isinstance(body.get("importResult"), dict) else None,
    )
    result["routeVersion"] = STATION_HANDOFF_ROUTE_VERSION
    return result
