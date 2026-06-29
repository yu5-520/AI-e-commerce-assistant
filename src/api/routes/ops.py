"""V12.14 Ops Diagnostic Train routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, Query, Request

from src.services.account_service import user_id_from_headers
from src.services.ops_diagnostic_train_service import check_single_station, get_ops_run, latest_ops_train, list_ops_runs, run_ops_train, station_health_summary

router = APIRouter(prefix="/api/ops", tags=["ops"])
OPS_ROUTE_VERSION = "12.14.0"


def request_user_id(request: Request) -> str:
    return user_id_from_headers(request.headers)


@router.post("/train/run")
def run_train(request: Request, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    return run_ops_train(mode=body.get("mode") or "contract", created_by=request_user_id(request))


@router.get("/train/latest")
def latest_train() -> Dict[str, Any]:
    return latest_ops_train()


@router.get("/train/runs")
def train_runs(limit: int = Query(default=20, ge=1, le=100)) -> Dict[str, Any]:
    return list_ops_runs(limit=limit)


@router.get("/train/runs/{run_id}")
def train_run_detail(run_id: str) -> Dict[str, Any]:
    return get_ops_run(run_id)


@router.get("/stations/health")
def ops_station_health() -> Dict[str, Any]:
    result = station_health_summary()
    result["routeVersion"] = OPS_ROUTE_VERSION
    return result


@router.post("/stations/{station_id}/check")
def ops_station_check(request: Request, station_id: str) -> Dict[str, Any]:
    return check_single_station(station_id, created_by=request_user_id(request))
