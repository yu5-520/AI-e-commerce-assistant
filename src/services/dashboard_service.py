"""Dashboard service for the modular backend.

The dashboard route should not directly depend on the old business view route
helpers. This service is the current boundary for homepage command-board data.
V3 adds a report-driven data refresh summary so the homepage can change after
new report snapshots trigger alerts and tasks.
"""

from __future__ import annotations

from typing import Any, Dict

from src.services.business_view_service import get_today_advice
from src.services.module_task_service import list_tasks
from src.services.report_alert_service import get_v3_dashboard_summary


def get_dashboard_summary() -> Dict[str, Any]:
    payload = get_today_advice(write_outputs=True, record_logs=True)
    active_tasks = list_tasks(active_only=True)[:5]
    v3_summary = get_v3_dashboard_summary()
    payload["tasks"] = active_tasks
    payload["api_entry"] = "/api/modules/dashboard"
    payload["service"] = "dashboard_service"
    payload["version"] = "3.0.0"
    payload["v3"] = v3_summary
    payload["data_refresh"] = {
        "title": "准实时数据更新",
        "latestDataVersion": v3_summary.get("latestDataVersion"),
        "latestSnapshotAt": v3_summary.get("latestSnapshotAt"),
        "activeAlertCount": v3_summary.get("activeAlertCount", 0),
        "highPriorityAlertCount": v3_summary.get("highPriorityAlertCount", 0),
        "taskLinkedAlertCount": v3_summary.get("taskLinkedAlertCount", 0),
        "message": "导入新报表后，首页、商品页、流量页、待办和日志会按预警事件同步刷新。",
    }
    payload["cards"] = [
        {"title": "新增预警", "value": v3_summary.get("activeAlertCount", 0), "desc": "来自最新报表"},
        {"title": "高风险", "value": v3_summary.get("highPriorityAlertCount", 0), "desc": "优先处理"},
        {"title": "已进待办", "value": v3_summary.get("taskLinkedAlertCount", 0), "desc": "任务同步"},
        {"title": "活跃任务", "value": len(active_tasks), "desc": "当前可处理"},
    ]
    return payload
