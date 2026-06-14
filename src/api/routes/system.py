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


@router.post("/clear-demo-data")
def clear_demo_runtime_data(
    confirm: bool = Query(default=False),
    include_audit_logs: bool = Query(default=True),
) -> Dict[str, Any]:
    """Clear generated demo runtime data after explicit confirmation."""
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Set confirm=true to clear generated demo runtime data.",
        )
    return clear_demo_data(include_audit_logs=include_audit_logs)
