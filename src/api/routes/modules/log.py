"""Log module routes."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

from src.services.module_task_service import list_logs

router = APIRouter()


@router.get("/log")
def log() -> List[Dict[str, Any]]:
    return list_logs()
