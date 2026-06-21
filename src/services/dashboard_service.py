"""Dashboard service for the V5 product demo runtime."""

from __future__ import annotations

from typing import Any, Dict

from src.services.module_projection_service import projection_summary
from src.services.module_task_service import list_tasks
from src.services.report_alert_service import get_v3_dashboard_summary


def get_dashboard_summary(user_id: str | None = None) -> Dict[str, Any]:
    active_tasks = list_tasks(viewer_id=user_id, active_only=True)[:5]
    v3_summary = get_v3_dashboard_summary(user_id)
    projection = projection_summary(user_id)
    has_data = bool(projection.get("hasData") or v3_summary.get("latestDataVersion"))
    return {
        "api_entry": "/api/modules/dashboard",
        "service": "dashboard_service",
        "version": "5.0.0",
        "hasData": has_data,
        "emptyState": "No data",
        "tasks": active_tasks,
        "v3": v3_summary,
        "projection": projection,
        "data_refresh": {
            "title": "Imported data runtime",
            "latestDataVersion": projection.get("latestDataVersion") or v3_summary.get("latestDataVersion"),
            "latestSnapshotAt": projection.get("latestSnapshotAt") or v3_summary.get("latestSnapshotAt"),
            "activeAlertCount": v3_summary.get("activeAlertCount", 0),
            "highPriorityAlertCount": v3_summary.get("highPriorityAlertCount", 0),
            "taskLinkedAlertCount": v3_summary.get("taskLinkedAlertCount", 0),
            "storeScoped": v3_summary.get("storeScoped", False),
            "message": "Dashboard only shows summaries produced after report imports.",
        },
        "cards": [
            {"title": "Data versions", "value": projection.get("dataVersionCount", 0), "desc": "current scope"},
            {"title": "Products", "value": projection.get("productCount", 0), "desc": "from imports"},
            {"title": "Alerts", "value": v3_summary.get("activeAlertCount", 0), "desc": "scoped"},
            {"title": "Tasks", "value": len(active_tasks), "desc": "active"},
        ],
    }
