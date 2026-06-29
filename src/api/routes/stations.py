"""V12.14 standard Station Interface routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException, Query, Request

from src.services.account_service import user_id_from_headers
from src.services.station_contract_service import list_station_contracts, run_station_contract, station_contract, station_gates, station_health
from src.services.station_registry_service import registry_summary, get_station

router = APIRouter(prefix="/api/stations", tags=["stations"])
STATION_ROUTE_VERSION = "12.14.0"


def request_user_id(request: Request) -> str:
    return user_id_from_headers(request.headers)


@router.get("")
def list_station_interfaces() -> Dict[str, Any]:
    registry = registry_summary()
    contracts = list_station_contracts()
    return {"version": STATION_ROUTE_VERSION, "registry": registry, "contracts": contracts.get("contracts"), "rule": "统一 Station Interface：前后端只认站点接口，不直接调用站点内部实现。"}


@router.get("/{station_id}")
def station_detail(station_id: str) -> Dict[str, Any]:
    station = get_station(station_id)
    if not station:
        raise HTTPException(status_code=404, detail="station not found")
    return {"version": STATION_ROUTE_VERSION, "station": station, "contract": station_contract(station_id), "health": station_health(station_id)}


@router.get("/{station_id}/contract")
def station_contract_endpoint(station_id: str) -> Dict[str, Any]:
    contract = station_contract(station_id)
    if not contract.get("ok"):
        raise HTTPException(status_code=404, detail="station not found")
    return contract


@router.get("/{station_id}/health")
def station_health_endpoint(station_id: str) -> Dict[str, Any]:
    health = station_health(station_id)
    if health.get("status") == "failed":
        raise HTTPException(status_code=404, detail="station not found")
    return health


@router.get("/{station_id}/gates")
def station_gates_endpoint(station_id: str, data_version: str | None = Query(default=None, alias="dataVersion"), limit: int = Query(default=40, ge=1, le=200)) -> Dict[str, Any]:
    return station_gates(station_id, data_version=data_version, limit=limit)


@router.get("/{station_id}/latest")
def station_latest_endpoint(station_id: str, data_version: str | None = Query(default=None, alias="dataVersion")) -> Dict[str, Any]:
    gates = station_gates(station_id, data_version=data_version, limit=1)
    return {"version": STATION_ROUTE_VERSION, "stationId": station_id, "latest": (gates.get("gates") or [None])[0], "gateCount": gates.get("gateCount", 0)}


@router.post("/{station_id}/run")
def run_station_endpoint(request: Request, station_id: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    body.setdefault("userId", request_user_id(request))
    result = run_station_contract(station_id, body, diagnostic=bool(body.get("isDiagnostic")))
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result)
    return result


@router.post("/{station_id}/replay")
def replay_station_endpoint(request: Request, station_id: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    body.setdefault("userId", request_user_id(request))
    body.setdefault("replay", True)
    result = run_station_contract(station_id, body, diagnostic=bool(body.get("isDiagnostic")))
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result)
    result["replayMode"] = True
    result["rule"] = "Replay 只重跑本站标准接口，下一站根据 outputRef 继续接力。"
    return result
