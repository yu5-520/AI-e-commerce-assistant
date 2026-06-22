"""Dashboard service for the V5 product runtime."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from src.services.module_projection_service import DATASET_LABELS, projection_summary, projected_products, projected_report_groups
from src.services.module_task_service import PRIORITY_RANK, list_tasks
from src.services.report_alert_service import get_v3_dashboard_summary

DASHBOARD_VERSION = "5.0.8"
DEADLINE_RANK = {"今天内": 1, "今日": 1, "明天前": 2, "明天": 2, "48小时内": 3, "本周内": 4}


def _short_time(value: str | None) -> str:
    if not value:
        return "已同步"
    text = str(value)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).strftime("%m-%d %H:%M")
    except ValueError:
        return text[-5:] if len(text) > 5 else text


def _count_value(text: Any) -> int:
    try:
        return int(str(text or "0").split()[0])
    except (TypeError, ValueError):
        return 0


def _deadline_rank(task: Dict[str, Any]) -> int:
    text = str(task.get("deadline") or task.get("timeBucket") or "本周内")
    for key, rank in DEADLINE_RANK.items():
        if key in text:
            return rank
    return 9


def _report_summary(groups: List[Dict[str, Any]], projection: Dict[str, Any]) -> Dict[str, Any]:
    imported: List[Dict[str, Any]] = []
    total_rows = 0
    for group in groups:
        for report in group.get("reports", []):
            rows = _count_value(report.get("count"))
            total_rows += rows
            if rows or report.get("status") == "已导入":
                imported.append(report)
    latest_dataset = projection.get("latestDatasetName")
    latest_label = DATASET_LABELS.get(latest_dataset, "最新数据") if latest_dataset else "暂无数据"
    latest_report = next((item for item in reversed(imported) if item.get("id") == latest_dataset), None) or (imported[-1] if imported else None)
    return {
        "label": latest_report.get("name") if latest_report else latest_label,
        "status": "已入库" if imported else "待导入",
        "rows": _count_value(latest_report.get("count")) if latest_report else 0,
        "totalRows": total_rows,
        "importedCount": len(imported),
        "affectedModules": ["报表", "总览", "商品"] if imported else [],
        "latestSyncedAt": _short_time(projection.get("latestSnapshotAt")),
        "technicalDataVersion": projection.get("latestDataVersion"),
        "technicalDatasetName": latest_dataset,
    }


def _task_title(task: Dict[str, Any]) -> str:
    product = task.get("productId") or task.get("entityId") or task.get("productShort") or "任务"
    domain = task.get("riskDomain") or task.get("taskType") or "经营"
    signal = task.get("taskSignal") or task.get("actionType") or "处理"
    if product and product != "任务":
        return f"{product}｜{domain}｜{signal}"
    return str(task.get("title") or task.get("taskType") or "经营任务")


def _task_queue(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sorted_tasks = sorted(tasks, key=lambda task: (PRIORITY_RANK.get(task.get("priority"), 9), _deadline_rank(task), task.get("manualOrder", 999999999), task.get("createdAt", "")))
    queue: List[Dict[str, Any]] = []
    for index, task in enumerate(sorted_tasks[:6], start=1):
        queue.append({
            "rank": index,
            "id": task.get("id"),
            "title": _task_title(task),
            "productId": task.get("productId") or task.get("entityId"),
            "riskDomain": task.get("riskDomain") or "经营",
            "priority": task.get("priority") or "中",
            "priorityLevel": task.get("priorityLevel") or "warning",
            "deadline": task.get("deadline") or "本周内",
            "status": task.get("workflowStatus") or task.get("status") or "待处理",
            "source": task.get("source") or task.get("sourceModule") or "任务池",
            "assigneeName": task.get("assigneeName") or "未派发",
            "reason": task.get("reason") or task.get("task") or "由导入数据生成。",
            "route": "business-actions",
        })
    return queue


def get_dashboard_summary(user_id: str | None = None) -> Dict[str, Any]:
    active_tasks = list_tasks(viewer_id=user_id, active_only=True)
    v3_summary = get_v3_dashboard_summary(user_id)
    projection = projection_summary(user_id)
    products = projected_products(user_id)
    reports = projected_report_groups(user_id)
    report_summary = _report_summary(reports, projection)
    has_data = bool(projection.get("hasData") or report_summary["importedCount"] or active_tasks)
    task_queue = _task_queue(active_tasks)
    high_tasks = [task for task in active_tasks if task.get("priority") == "高"]
    return {
        "apiEntry": "/api/modules/dashboard",
        "version": DASHBOARD_VERSION,
        "hasData": has_data,
        "emptyState": "暂无数据",
        "title": "经营总览",
        "heroBadge": report_summary["status"] if has_data else "数据驱动",
        "latestImport": report_summary,
        "metrics": [
            {"label": "最新数据", "value": report_summary["label"], "desc": report_summary["status"]},
            {"label": "报表", "value": f"{report_summary['totalRows']} 条", "desc": f"{report_summary['importedCount']} 份已入库"},
            {"label": "商品", "value": len(products), "desc": "已进入商品栏"},
            {"label": "任务", "value": len(active_tasks), "desc": f"高优先级 {len(high_tasks)}"},
        ],
        "taskQueue": task_queue,
        "tasks": active_tasks[:6],
        "v3": v3_summary,
        "projection": projection,
    }
