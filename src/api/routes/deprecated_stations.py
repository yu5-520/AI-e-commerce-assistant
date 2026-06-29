"""V12.14.2 Deprecated Station Archive routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from src.services.deprecated_station_registry_service import deprecated_summary, get_deprecated_item, mainline_purity_check

router = APIRouter(prefix="/api/deprecated-stations", tags=["deprecated-stations"])
DEPRECATED_STATION_ROUTE_VERSION = "12.14.2"


@router.get("")
def list_deprecated_stations() -> Dict[str, Any]:
    summary = deprecated_summary()
    summary["routeVersion"] = DEPRECATED_STATION_ROUTE_VERSION
    return summary


@router.get("/risks")
def deprecated_station_risks() -> Dict[str, Any]:
    summary = deprecated_summary()
    check = mainline_purity_check()
    return {
        "version": DEPRECATED_STATION_ROUTE_VERSION,
        "status": check.get("status"),
        "highRiskCount": summary.get("highRiskCount"),
        "adapterWhitelistCount": summary.get("adapterWhitelistCount"),
        "violations": check.get("violations", []),
        "warnings": check.get("warnings", []),
        "rule": "风险页只审计旧文件是否回流主线，不参与业务流程。",
    }


@router.get("/mainline-check")
def deprecated_mainline_check() -> Dict[str, Any]:
    result = mainline_purity_check()
    result["routeVersion"] = DEPRECATED_STATION_ROUTE_VERSION
    return result


@router.get("/{legacy_id}")
def deprecated_station_detail(legacy_id: str) -> Dict[str, Any]:
    item = get_deprecated_item(legacy_id)
    if not item:
        raise HTTPException(status_code=404, detail="deprecated station item not found")
    return {"version": DEPRECATED_STATION_ROUTE_VERSION, "item": item}
