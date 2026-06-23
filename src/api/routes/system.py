"""System status routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query

from src.core.context import UserContext, get_current_context
from src.services.repository_runtime_service import repository_health_check, repository_runtime_summary
from src.services.security_status_service import security_status
from src.services.system_service import clear_runtime_data as clear_runtime_store
from src.services.system_service import get_db_status, reset_legacy_runtime_once

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/db-status")
def db_status() -> Dict[str, Any]:
    """Return SQLite database file and table status."""
    return get_db_status()


@router.get("/security")
def system_security(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Return deployment security, rate limit, worker, LLM, and log redaction status."""
    return security_status(ctx)


@router.get("/repositories")
async def repository_runtime(check: bool = Query(default=False), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Return repository transition mode and optionally check PostgreSQL connectivity."""
    if check:
        return await repository_health_check(ctx)
    return repository_runtime_summary(ctx)


def _clear_runtime_data(confirm: bool, include_audit_logs: bool, reason: str = "manual_reset") -> Dict[str, Any]:
    if not confirm:
        raise HTTPException(status_code=400, detail="Set confirm=true to clear generated runtime data.")
    return clear_runtime_store(include_audit_logs=include_audit_logs, reason=reason)


@router.post("/reset-runtime-data")
def reset_runtime_data(confirm: bool = Query(default=False), include_audit_logs: bool = Query(default=True)) -> Dict[str, Any]:
    """Clear V5 generated runtime data and return to true empty state."""
    return _clear_runtime_data(confirm=confirm, include_audit_logs=include_audit_logs, reason="manual_v5_runtime_reset")


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
    """Apply the V5 one-time cleanup marker and remove stale pre-V5 runtime rows."""
    return reset_legacy_runtime_once()
