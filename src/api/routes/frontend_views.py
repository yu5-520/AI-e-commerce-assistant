"""V16.3 read-only frontend view routes.

These endpoints are for page rendering and验收 only. They read cached read-model
tables and must not trigger materialize/generate/Agent/worker execution. Task
views are current-run isolated by dataVersion, and /task-pool-acceptance proves
that data-line, task_pool and frontend task views align.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Query

from src.services.frontend_read_model_service import (
    FRONTEND_READ_MODEL_VERSION,
    read_dashboard_view,
    read_product_detail,
    read_product_views,
    read_system_status_view,
    read_task_detail,
    read_task_views,
    refresh_all_read_models,
)
from src.services.task_generation_run_service import read_data_line_status
from src.services.task_pool_acceptance_v163_service import read_task_pool_acceptance

router = APIRouter(prefix="/api/view", tags=["frontend-read-model"])


@router.get("/dashboard")
def dashboard_view() -> Dict[str, Any]:
    result = read_dashboard_view()
    result["routeRule"] = "read_only_frontend_view_no_compute_current_run_isolated"
    return result


@router.get("/products")
def product_view(storeId: str | None = None, dataVersion: str | None = None, limit: int = Query(default=200, ge=1, le=500)) -> Dict[str, Any]:
    result = read_product_views(store_id=storeId, data_version=dataVersion, limit=limit)
    result["routeRule"] = "read_only_frontend_view_no_compute_current_run_isolated"
    return result


@router.get("/products/{product_id}")
def product_detail_view(product_id: str, storeId: str | None = None) -> Dict[str, Any]:
    result = read_product_detail(product_id, store_id=storeId)
    result["routeRule"] = "read_only_frontend_view_no_compute_current_run_isolated"
    return result


@router.get("/tasks")
def task_view(status: str | None = None, dataVersion: str | None = None, limit: int = Query(default=200, ge=1, le=500)) -> Dict[str, Any]:
    result = read_task_views(status=status, data_version=dataVersion, limit=limit)
    result["routeRule"] = "read_only_frontend_view_no_compute_current_run_isolated"
    return result


@router.get("/tasks/{task_id}")
def task_detail_view(task_id: str) -> Dict[str, Any]:
    result = read_task_detail(task_id)
    result["routeRule"] = "read_only_frontend_view_no_compute_current_run_isolated"
    return result


@router.get("/system-status")
def system_status_view() -> Dict[str, Any]:
    result = read_system_status_view()
    result["routeRule"] = "read_only_frontend_view_no_compute"
    return result


@router.get("/data-line")
def data_line_view() -> Dict[str, Any]:
    result = read_data_line_status()
    acceptance = read_task_pool_acceptance(data_version=result.get("dataVersion")) if result.get("dataVersion") else read_task_pool_acceptance()
    result["taskPoolAcceptance"] = acceptance
    if acceptance.get("status") == "failed" and result.get("lineStatus") == "completed":
        result["lineStatus"] = "attention"
        result["headline"] = f"本轮任务池验收未通过：{len(acceptance.get('mismatches') or [])} 个断点"
    result["routeRule"] = "read_only_frontend_view_no_compute_with_v163_task_pool_acceptance"
    return result


@router.get("/task-pool-acceptance")
def task_pool_acceptance_view(dataVersion: str | None = None) -> Dict[str, Any]:
    result = read_task_pool_acceptance(data_version=dataVersion)
    result["routeRule"] = "read_only_acceptance_no_compute_no_agent"
    return result


@router.get("/stores")
def store_view() -> Dict[str, Any]:
    products = read_product_views(limit=500)
    stores: Dict[str, Dict[str, Any]] = {}
    for item in products.get("items") or []:
        store_id = item.get("storeId") or "UNKNOWN"
        store = stores.setdefault(store_id, {"storeId": store_id, "storeName": item.get("storeName") or "经营单元", "platform": item.get("platform"), "productCount": 0, "highRiskProductCount": 0, "updatedAt": item.get("updatedAt")})
        store["productCount"] += 1
        if item.get("signalStrength") == "high":
            store["highRiskProductCount"] += 1
    return {"version": FRONTEND_READ_MODEL_VERSION, "ready": bool(stores), "count": len(stores), "currentDataVersion": products.get("currentDataVersion"), "items": list(stores.values()), "routeRule": "read_only_frontend_view_no_compute_current_run_isolated"}


@router.post("/refresh")
def refresh_views(dataVersion: str | None = None) -> Dict[str, Any]:
    result = refresh_all_read_models(data_version=dataVersion)
    result["taskPoolAcceptance"] = read_task_pool_acceptance(data_version=dataVersion)
    result["routeRule"] = "explicit_compute_endpoint_current_run_isolated_then_acceptance"
    return result
