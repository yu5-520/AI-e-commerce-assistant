"""V5 projected report module routes."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request

from src.api.routes.modules.common import find_or_404
from src.services.account_service import user_id_from_headers
from src.services.module_data_service import all_reports
from src.services.module_projection_service import projected_report_details, projected_report_groups
from src.services.module_task_service import create_task
from src.services.report_alert_service import get_v3_dashboard_summary, list_alert_events
from src.services.v1211_manual_task_package_service import wrap_manual_task_payload

router = APIRouter()
REPORT_MODULE_VERSION = "12.11.1"


def request_user_id(request: Request) -> str:
    return user_id_from_headers(request.headers)


def _flatten(groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [report for group in groups for report in group.get("reports", [])]


def _real_sync_records(groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for group in groups:
        for report in group.get("reports", []):
            if not report.get("latestDataVersion") and report.get("status") != "已导入":
                continue
            records.append({
                "id": report.get("id"),
                "name": report.get("name") or report.get("id") or "同步记录",
                "label": report.get("name") or report.get("id") or "同步记录",
                "status": report.get("status") or "已处理",
                "count": report.get("count") or "0 条",
                "source": report.get("source") or group.get("name") or "数据源",
                "latestDataVersion": report.get("latestDataVersion"),
                "latestSnapshotAt": report.get("latestSnapshotAt"),
                "createdTaskCount": int(report.get("createdTaskCount") or report.get("taskCount") or 0),
            })
    return records


def report_task_payload(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "entityType": "报表",
        "entityId": item["id"],
        "riskDomain": "报表",
        "actionType": "复盘",
        "sourceModule": "报表模块",
        "source": "报表触发",
        "sourceRoute": "data-check",
        "productId": f"R-{item['id']}",
        "imageLabel": "表",
        "productShort": item.get("name") or item["id"],
        "productTitle": f"{item.get('name') or item['id']}导入后复盘",
        "title": f"{item.get('name') or item['id']}导入后复盘",
        "platform": item.get("source") or "报表",
        "store": "按账号权限切片",
        "priority": "高" if item.get("id") in {"refunds", "orders"} else "中",
        "priorityLevel": "danger" if item.get("id") in {"refunds", "orders"} else "warning",
        "deadline": "今天内" if item.get("id") in {"refunds", "orders"} else "本周内",
        "taskType": "报表复盘",
        "taskSignal": "导入后生成任务",
        "task": f"复盘{item.get('name') or item['id']}，检查模块内容、预警和任务归属。",
        "reason": f"{item.get('desc', '')}。当前导入状态：{item.get('status', '待导入')}，数据量：{item.get('count', '0 条')}。",
        "judgmentTags": [item.get("source", "报表"), item.get("status", "待导入"), item.get("count", "0 条")],
        "sourceDataVersion": item.get("latestDataVersion"),
    }


@router.get("/report")
def report(request: Request) -> Dict[str, Any]:
    user_id = request_user_id(request)
    groups = projected_report_groups(user_id)
    details = projected_report_details(user_id)
    v3 = get_v3_dashboard_summary(user_id)
    recent_alerts = list_alert_events(limit=10, active_only=True, user_id=user_id)
    sync_records = _real_sync_records(groups)
    has_data = bool(sync_records or details or v3.get("latestDataVersion") or recent_alerts)
    return {
        "version": REPORT_MODULE_VERSION,
        "hasData": has_data,
        "reportGroups": groups if has_data else [],
        "reportDetails": details if has_data else {},
        "syncRecords": sync_records,
        "v3": v3 if has_data else {"version": v3.get("version"), "activeAlertCount": 0, "highPriorityAlertCount": 0, "latestAlerts": []},
        "recentAlerts": recent_alerts if has_data else [],
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


@router.post("/report/{report_id}/tasks")
def report_task(request: Request, report_id: str) -> Dict[str, Any]:
    user_id = request_user_id(request)
    reports = _flatten(projected_report_groups(user_id)) or all_reports()
    item = find_or_404(reports, report_id, "report")
    return create_task(wrap_manual_task_payload(report_task_payload(item)))
