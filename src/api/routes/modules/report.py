"""Report module routes."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request

from src.api.routes.modules.common import find_or_404
from src.services.account_service import user_id_from_headers
from src.services.module_data_service import REPORT_DETAILS, REPORT_GROUPS, all_reports, clone
from src.services.module_task_service import attach_task_state, create_task
from src.services.report_alert_service import get_v3_dashboard_summary, list_alert_events

router = APIRouter()


def request_user_id(request: Request) -> str:
    return user_id_from_headers(request.headers)


def report_task_payload(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "entityType": "报表",
        "entityId": item["id"],
        "riskDomain": "报表",
        "actionType": "导入",
        "sourceModule": "ERP / CRM 报表管理",
        "source": "报表触发",
        "sourceRoute": "data-check",
        "productId": f"R-{item['id']}",
        "imageLabel": "表",
        "productShort": item["name"],
        "productTitle": f"{item['name']}导入后复盘",
        "title": f"{item['name']}导入后复盘",
        "platform": item["source"],
        "store": "家居生活店铺组",
        "productRoute": "data-check",
        "priority": "高" if item["id"] in {"refunds", "orders"} else "中",
        "priorityLevel": "danger" if item["id"] in {"refunds", "orders"} else "warning",
        "deadline": "今天内" if item["id"] in {"refunds", "orders"} else "本周内",
        "taskType": "报表复盘",
        "taskSignal": "导入后生成任务",
        "task": f"复盘{item['name']}，生成下一轮经营任务",
        "reason": f"{item['desc']}。导入后需要同步首页、待办和日志。",
        "judgmentTags": [item["source"], item["status"], item["count"]],
    }


def annotated_report_groups(user_id: str | None = None) -> List[Dict[str, Any]]:
    groups = []
    v3_summary = get_v3_dashboard_summary(user_id)
    for group in REPORT_GROUPS:
        next_group = {**group, "reports": []}
        for item in group["reports"]:
            annotated = attach_task_state(item, report_task_payload(item))
            if annotated.get("candidateArchived"):
                continue
            annotated["dataRefreshState"] = {
                "latestDataVersion": v3_summary.get("latestDataVersion"),
                "latestSnapshotAt": v3_summary.get("latestSnapshotAt"),
                "activeAlertCount": v3_summary.get("alertByDataset", {}).get(item["id"], 0),
                "globalAlertCount": v3_summary.get("activeAlertCount", 0),
                "storeScoped": v3_summary.get("storeScoped", False),
            }
            next_group["reports"].append(annotated)
        if next_group["reports"]:
            groups.append(next_group)
    return groups


@router.get("/report")
def report(request: Request) -> Dict[str, Any]:
    user_id = request_user_id(request)
    return {
        "reportGroups": annotated_report_groups(user_id),
        "reportDetails": clone(REPORT_DETAILS),
        "v3": get_v3_dashboard_summary(user_id),
        "recentAlerts": list_alert_events(limit=10, active_only=True, user_id=user_id),
    }


@router.get("/report/{report_id}")
def report_detail(request: Request, report_id: str) -> Dict[str, Any]:
    if report_id not in REPORT_DETAILS:
        raise HTTPException(status_code=404, detail="report not found")
    user_id = request_user_id(request)
    detail = clone(REPORT_DETAILS[report_id])
    detail["v3"] = get_v3_dashboard_summary(user_id)
    detail["relatedAlerts"] = [alert for alert in list_alert_events(limit=50, user_id=user_id) if alert.get("sourceDataset") == report_id]
    return detail


@router.post("/report/{report_id}/tasks")
def report_task(report_id: str) -> Dict[str, Any]:
    item = find_or_404(all_reports(), report_id, "report")
    return create_task(report_task_payload(item))
