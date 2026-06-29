"""V14.1 projected report module routes."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request

from src.api.routes.modules.common import find_or_404
from src.services.account_service import user_id_from_headers
from src.services.module_data_service import all_reports
from src.services.module_projection_service import projected_report_details, projected_report_groups
from src.services.report_alert_service import get_v3_dashboard_summary, list_alert_events
from src.services.task_pool_station_service import enter_task_pool_from_snapshot
from src.services.task_snapshot_station_service import create_task_snapshot

router = APIRouter()
REPORT_MODULE_VERSION = "14.1.0"


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
            records.append({"id": report.get("id"), "name": report.get("name") or report.get("id") or "同步记录", "label": report.get("name") or report.get("id") or "同步记录", "status": report.get("status") or "已处理", "count": report.get("count") or "0 条", "source": report.get("source") or group.get("name") or "数据源", "latestDataVersion": report.get("latestDataVersion"), "latestSnapshotAt": report.get("latestSnapshotAt"), "createdTaskCount": int(report.get("createdTaskCount") or report.get("taskCount") or 0)})
    return records


def report_task_payload(item: Dict[str, Any]) -> Dict[str, Any]:
    return {"entityType": "报表", "entityId": item["id"], "riskDomain": "报表", "actionType": "复盘", "sourceModule": "报表模块", "source": "报表模块触发", "sourceRoute": "data-check", "productId": f"R-{item['id']}", "imageLabel": "表", "productShort": item.get("name") or item["id"], "productTitle": f"{item.get('name') or item['id']}导入后复盘", "title": f"{item.get('name') or item['id']}导入后复盘", "platform": item.get("source") or "报表", "store": "按账号权限切片", "priority": "高" if item.get("id") in {"refunds", "orders"} else "中", "priorityLevel": "danger" if item.get("id") in {"refunds", "orders"} else "warning", "deadline": "今天内" if item.get("id") in {"refunds", "orders"} else "本周内", "taskType": "报表复盘", "taskSignal": "模块页面人工请求", "task": f"复盘{item.get('name') or item['id']}，检查模块内容、预警和任务归属。", "reason": f"{item.get('desc', '')}。当前导入状态：{item.get('status', '待导入')}，数据量：{item.get('count', '0 条')}。", "judgmentTags": [item.get("source", "报表"), item.get("status", "待导入"), item.get("count", "0 条")], "sourceDataVersion": item.get("latestDataVersion")}


def _enter_snapshot_pool(payload: Dict[str, Any], user_id: str | None = None) -> Dict[str, Any]:
    entity_id = payload.get("entityId") or payload.get("productId")
    data_version = payload.get("sourceDataVersion") or payload.get("dataVersion")
    priority = payload.get("priority") or "中"
    decision = "manager_review_required" if priority == "高" else "create_task_snapshot"
    task_plan = {"title": payload.get("title") or entity_id, "subtitle": "manual_report_request_v14_1", "entityType": payload.get("entityType") or "报表", "entityId": entity_id, "taskType": payload.get("taskType") or "报表复核", "actionType": payload.get("actionType") or "manual_report_request", "priority": priority, "deadline": payload.get("deadline") or "24小时内", "riskDomain": payload.get("riskDomain") or "报表", "sopSteps": [payload.get("task") or "复核报表同步状态。", "提交异常字段、数据口径和影响范围。", "后续由系统复盘相关指标。"], "evidenceRequirements": ["报表来源", "异常字段", "处理说明"], "reviewMetrics": ["入库行数", "识别字段数", "任务信号数", "数据缺口数"], "needManagerReview": decision == "manager_review_required", "reason": payload.get("reason") or payload.get("taskSignal")}
    snapshot = create_task_snapshot({"dataVersion": data_version, "decision": decision, "confidence": 0.7, "entityType": payload.get("entityType") or "报表", "entityId": entity_id, "signalRef": f"manual:report:{entity_id}:{data_version or 'latest'}", "ragContext": {"source": "report_manual_request", "version": REPORT_MODULE_VERSION}, "agentJudgment": {"decision": decision, "confidence": 0.7, "reason": task_plan["reason"], "status": "manual_snapshot_bridge"}, "taskPlan": task_plan, "evidenceRequirements": task_plan["evidenceRequirements"], "systemFacts": {"modulePayload": payload}, "source": "report_module_manual_request"}, created_by=user_id)
    pool = enter_task_pool_from_snapshot(snapshot.get("taskSnapshotId"), created_by=user_id)
    return {"version": REPORT_MODULE_VERSION, "mode": "manual_request_via_task_snapshot", "snapshot": snapshot, "pool": pool, "task": pool.get("task") if isinstance(pool, dict) else None}


@router.get("/report")
def report(request: Request) -> Dict[str, Any]:
    user_id = request_user_id(request)
    groups = projected_report_groups(user_id)
    details = projected_report_details(user_id)
    v3 = get_v3_dashboard_summary(user_id)
    recent_alerts = list_alert_events(limit=10, active_only=True, user_id=user_id)
    sync_records = _real_sync_records(groups)
    has_data = bool(sync_records or details or v3.get("latestDataVersion") or recent_alerts)
    return {"version": REPORT_MODULE_VERSION, "hasData": has_data, "reportGroups": groups if has_data else [], "reportDetails": details if has_data else {}, "syncRecords": sync_records, "v3": v3 if has_data else {"version": v3.get("version"), "activeAlertCount": 0, "highPriorityAlertCount": 0, "latestAlerts": []}, "recentAlerts": recent_alerts if has_data else []}


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
    return _enter_snapshot_pool(report_task_payload(item), user_id=user_id)
