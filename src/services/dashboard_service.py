"""Dashboard service for the modular backend.

The dashboard route should not directly depend on the old business view route
helpers. This service is the current boundary for homepage command-board data
until the workflow summary is fully migrated into dedicated module services.
"""

from __future__ import annotations

from typing import Any, Dict

from src.services.business_view_service import get_today_advice
from src.services.module_task_service import list_tasks


def get_dashboard_summary() -> Dict[str, Any]:
    payload = get_today_advice(write_outputs=True, record_logs=True)
    payload["tasks"] = list_tasks(active_only=True)[:5]
    payload["api_entry"] = "/api/modules/dashboard"
    payload["service"] = "dashboard_service"
    return payload
