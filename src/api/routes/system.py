"""System status routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from src.services.system_service import get_db_status

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/db-status")
def db_status() -> Dict[str, Any]:
    """Return SQLite database file and table status."""
    return get_db_status()
