"""System status routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from src.services.system_service import clear_demo_data, get_db_status

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/db-status")
def db_status() -> Dict[str, Any]:
    """Return SQLite database file and table status."""
    return get_db_status()


def _clear_runtime_data(confirm: bool, include_audit_logs: bool) -> Dict[str, Any]:
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Set confirm=true to clear generated runtime data.",
        )
    return clear_demo_data(include_audit_logs=include_audit_logs)


@router.post("/clear-runtime-data")
def clear_runtime_data(
    confirm: bool = Query(default=False),
    include_audit_logs: bool = Query(default=True),
) -> Dict[str, Any]:
    """Clear generated runtime data after explicit confirmation."""
    return _clear_runtime_data(confirm=confirm, include_audit_logs=include_audit_logs)


@router.post("/clear-demo-data")
def clear_demo_runtime_data(
    confirm: bool = Query(default=False),
    include_audit_logs: bool = Query(default=True),
) -> Dict[str, Any]:
    """Backward-compatible alias for `/api/system/clear-runtime-data`."""
    return _clear_runtime_data(confirm=confirm, include_audit_logs=include_audit_logs)
