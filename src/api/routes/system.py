"""V16.23 system routes.

System routes keep the MVP runtime utilities that are still needed during report
import testing: database status and explicit runtime cleanup. Old production
readiness diagnostics that depended on the deleted src.core.context module are
returned as disabled V16-safe projections instead of importing legacy context.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query, Request

from src.services.account_service import current_user, user_id_from_headers
from src.services.system_service import clear_runtime_data as clear_runtime_store
from src.services.system_service import get_db_status, reset_legacy_runtime_once

router = APIRouter(prefix="/api/system", tags=["system"])
SYSTEM_ROUTE_VERSION = "16.23"


def request_user_id(request: Request) -> str:
    return user_id_from_headers(request.headers)


def request_context_meta(request: Request) -> Dict[str, Any]:
    user_id = request_user_id(request)
    user = current_user(user_id)
    return {
        "userId": user_id,
        "roleId": user.get("roleId") or user.get("role_id") or "operator",
        "tenantId": user.get("tenantId") or user.get("tenant_id") or "demo_tenant",
        "source": "v16_system_route_no_src_core_context",
    }


def disabled_legacy_system_view(name: str, request: Request, extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return {
        "version": SYSTEM_ROUTE_VERSION,
        "name": name,
        "status": "disabled_in_v16_mvp_runtime",
        "scope": request_context_meta(request),
        "extra": extra or {},
        "rule": "V16.23：系统路由不再导入src.core.context；旧生产诊断接口只保留轻量占位，MVP保留db-status和清空数据接口。",
    }


@router.get("/db-status")
def db_status() -> Dict[str, Any]:
    """Return SQLite database file and table status."""
    result = get_db_status()
    if isinstance(result, dict):
        result.setdefault("version", SYSTEM_ROUTE_VERSION)
    return result


@router.get("/runtime-diagnostics")
def runtime_object_diagnostics(request: Request) -> Dict[str, Any]:
    """Legacy runtime diagnostics placeholder."""
    return disabled_legacy_system_view("runtime-diagnostics", request)


@router.post("/backfill-operating-objects")
def backfill_operating_object_store(request: Request) -> Dict[str, Any]:
    """Legacy backfill placeholder; import path now owns V16 object materialization."""
    return disabled_legacy_system_view("backfill-operating-objects", request, {"replacement": "data_import -> operating_object_sync"})


@router.get("/security")
def system_security(request: Request) -> Dict[str, Any]:
    """Return a V16-safe security placeholder without loading legacy diagnostics."""
    return disabled_legacy_system_view("security", request)


@router.get("/isolation")
def backend_isolation(request: Request) -> Dict[str, Any]:
    """Return a lightweight isolation view for MVP runtime."""
    return {
        "version": SYSTEM_ROUTE_VERSION,
        "status": "v16_mvp_lightweight",
        "currentContext": request_context_meta(request),
        "rule": "V16.23 lightweight context only; no src.core.context dependency.",
    }


@router.get("/repositories")
async def repository_runtime(request: Request, check: bool = Query(default=False)) -> Dict[str, Any]:
    """Legacy repository transition view placeholder."""
    return disabled_legacy_system_view("repositories", request, {"check": check})


@router.get("/postgres-cutover-check")
async def postgres_cutover(request: Request) -> Dict[str, Any]:
    """Legacy PostgreSQL cutover check placeholder."""
    return disabled_legacy_system_view("postgres-cutover-check", request)


def _clear_runtime_data(confirm: bool, include_audit_logs: bool, reason: str = "manual_reset") -> Dict[str, Any]:
    if not confirm:
        raise HTTPException(status_code=400, detail="Set confirm=true to clear generated runtime data.")
    result = clear_runtime_store(include_audit_logs=include_audit_logs, reason=reason)
    if isinstance(result, dict):
        result.setdefault("version", SYSTEM_ROUTE_VERSION)
        result.setdefault("routeRule", "v16_system_cleanup_no_legacy_context")
    return result


@router.post("/reset-runtime-data")
def reset_runtime_data(confirm: bool = Query(default=False), include_audit_logs: bool = Query(default=True)) -> Dict[str, Any]:
    """Clear generated runtime data and return to test-ready state."""
    return _clear_runtime_data(confirm=confirm, include_audit_logs=include_audit_logs, reason="manual_v16_runtime_reset")


@router.post("/clear-runtime-data")
def clear_runtime_data(confirm: bool = Query(default=False), include_audit_logs: bool = Query(default=True)) -> Dict[str, Any]:
    """Clear generated runtime data after explicit confirmation."""
    return _clear_runtime_data(confirm=confirm, include_audit_logs=include_audit_logs, reason="manual_clear_runtime_data")


@router.post("/clear-demo-data")
def clear_demo_runtime_data(confirm: bool = Query(default=False), include_audit_logs: bool = Query(default=True)) -> Dict[str, Any]:
    """Backward-compatible alias for `/api/system/clear-runtime-data`."""
    return _clear_runtime_data(confirm=confirm, include_audit_logs=include_audit_logs, reason="manual_clear_demo_data_alias")


@router.post("/reset-legacy-runtime-once")
def reset_legacy_runtime() -> Dict[str, Any]:
    """Apply the one-time cleanup marker and remove stale legacy runtime rows."""
    result = reset_legacy_runtime_once()
    if isinstance(result, dict):
        result.setdefault("version", SYSTEM_ROUTE_VERSION)
        result.setdefault("routeRule", "v16_system_legacy_marker_cleanup")
    return result
