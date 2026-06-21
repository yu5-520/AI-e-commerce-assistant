"""Operating unit route for V5 projection data."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Request

from src.services.account_service import current_user, user_id_from_headers
from src.services.module_projection_service import projection_summary, projected_products, projected_report_groups, projected_traffic
from src.services.module_task_service import get_task_counters_for_user
from src.services.report_alert_service import get_v3_dashboard_summary

router = APIRouter()


def _report_rows(groups: list[Dict[str, Any]]) -> int:
    total = 0
    for group in groups:
        for report in group.get("reports", []):
            text = str(report.get("count") or "0").split()[0]
            try:
                total += int(text)
            except ValueError:
                continue
    return total


@router.get("/operating-unit")
def operating_unit(request: Request) -> Dict[str, Any]:
    user_id = user_id_from_headers(request.headers)
    user = current_user(user_id)
    projection = projection_summary(user_id)
    v3 = get_v3_dashboard_summary(user_id)
    products = projected_products(user_id)
    traffic = projected_traffic(user_id)
    reports = projected_report_groups(user_id)
    task_counters = get_task_counters_for_user(user_id)
    has_data = bool(projection.get("hasData") or v3.get("latestDataVersion") or products or traffic or v3.get("activeAlertCount"))
    if not has_data:
        return {
            "version": "5.0.4",
            "hasData": False,
            "emptyState": "暂无数据",
            "viewer": {"id": user.get("id"), "roleId": user.get("roleId"), "roleName": user.get("roleName")},
            "metrics": [],
            "agents": [],
            "tasks": {},
        }
    return {
        "version": "5.0.4",
        "hasData": True,
        "unitName": "经营单元",
        "latestDataVersion": projection.get("latestDataVersion") or v3.get("latestDataVersion"),
        "latestSnapshotAt": projection.get("latestSnapshotAt") or v3.get("latestSnapshotAt"),
        "viewer": {"id": user.get("id"), "roleId": user.get("roleId"), "roleName": user.get("roleName")},
        "metrics": [
            {"label": "商品", "value": len(products)},
            {"label": "流量", "value": len(traffic)},
            {"label": "报表行", "value": _report_rows(reports)},
            {"label": "预警", "value": v3.get("activeAlertCount", 0)},
            {"label": "任务", "value": task_counters.get("visibleActive", 0)},
        ],
        "agents": [
            {"name": "经营单元 Agent", "status": "待增强", "basis": "ModuleProjection"},
            {"name": "回流 Agent", "status": "待复核", "basis": "任务完成记录"},
            {"name": "RAG Memory", "status": "复核后入库", "basis": "经验卡"},
        ],
        "tasks": task_counters,
        "projection": projection,
        "v3": v3,
    }
