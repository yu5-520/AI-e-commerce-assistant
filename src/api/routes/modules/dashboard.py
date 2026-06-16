"""Dashboard module route."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from src.services.business_view_service import get_today_advice
from src.services.module_task_service import list_tasks

router = APIRouter()


@router.get("/dashboard")
def dashboard() -> Dict[str, Any]:
    payload = get_today_advice(write_outputs=True, record_logs=True)
    payload["tasks"] = list_tasks(active_only=True)[:5]
    payload["api_entry"] = "/api/modules/dashboard"
    return payload
