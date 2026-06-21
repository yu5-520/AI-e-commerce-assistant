"""V5 projected report module routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request

from src.services.account_service import user_id_from_headers
from src.services.module_projection_service import projected_report_details, projected_report_groups
from src.services.report_alert_service import get_v3_dashboard_summary, list_alert_events

router = APIRouter()


def request_user_id(request: Request) -> str:
    return user_id_from_headers(request.headers)


@router.get("/report")
def report(request: Request) -> Dict[str, Any]:
    user_id = request_user_id(request)
    return {
        "reportGroups": projected_report_groups(user_id),
        "reportDetails": projected_report_details(user_id),
        "v3": get_v3_dashboard_summary(user_id),
        "recentAlerts": list_alert_events(limit=10, active_only=True, user_id=user_id),
    }


@router.get("/report/{report_id}")
def report_detail(request: Request, report_id: str) -> Dict[str, Any]:
    user_id = request_user_id(request)
    details = projected_report_details(user_id)
    if report_id not in details:
        raise HTTPException(status_code=404, detail="report not found")
    detail = details[report_id]
    detail["v3"] = get_v3_dashboard_summary(user_id)
    detail["relatedAlerts"] = [alert for alert in list_alert_events(limit=50, user_id=user_id) if alert.get("sourceDataset") == report_id]
    return detail
