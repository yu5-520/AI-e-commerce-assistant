"""Dashboard service for the V10.3 task workbench runtime."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from src.services.module_projection_service import DATASET_LABELS, projection_summary, projected_products, projected_report_groups
from src.services.module_task_service import DONE_STATUS, PRIORITY_RANK, get_task_counters_for_user, list_logs, list_tasks
from src.services.report_alert_service import get_v3_dashboard_summary

DASHBOARD_VERSION = "10.3.0"
DEADLINE_RANK = {"今天内": 1, "今日": 1, "明天前": 2, "明天": 2, "48小时内": 3, "本周内": 4}
DASHBOARD_WORKBENCH_SECTIONS = ["todayPriorityTasks", "highRiskItems", "latestReportResult", "pendingReviewItems", "completionProgress"]


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
        "affectedModules": ["报表", "总览", "经营", "任务"] if imported else [],
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


def _task_card(task: Dict[str, Any], rank: int) -> Dict[str, Any]:
    return {
        "rank": rank,
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
        "reviewerName": task.get("reviewerName") or "待复核人",
        "reason": task.get("reason") or task.get("task") or "由导入数据生成。",
        "route": "business-actions",
    }


def _task_queue(tasks: List[Dict[str, Any]], limit: int = 6) -> List[Dict[str, Any]]:
    sorted_tasks = sorted(tasks, key=lambda task: (PRIORITY_RANK.get(task.get("priority"), 9), _deadline_rank(task), task.get("manualOrder", 999999999), task.get("createdAt", "")))
    return [_task_card(task, index) for index, task in enumerate(sorted_tasks[:limit], start=1)]


def _is_high_risk(task: Dict[str, Any]) -> bool:
    return task.get("priority") == "高" or task.get("priorityLevel") == "danger" or "高风险" in " ".join(task.get("judgmentTags") or [])


def _is_review_task(task: Dict[str, Any]) -> bool:
    return task.get("status") in {"待复核", "已提交"} or task.get("workflowStatus") in {"待复核", "已提交"}


def _dashboard_workbench(active_tasks: List[Dict[str, Any]], all_tasks: List[Dict[str, Any]], report_summary: Dict[str, Any], counters: Dict[str, Any]) -> Dict[str, Any]:
    priority_tasks = _task_queue(active_tasks, limit=5)
    high_risk = _task_queue([task for task in active_tasks if _is_high_risk(task)], limit=3)
    review_items = _task_queue([task for task in active_tasks if _is_review_task(task)], limit=3)
    completed_count = len([task for task in all_tasks if task.get("status") in DONE_STATUS])
    total_count = max(len(all_tasks), completed_count + len(active_tasks), 1)
    completion_rate = round(completed_count / total_count * 100)
    report_result = {
        "label": report_summary.get("label"),
        "status": report_summary.get("status"),
        "summary": f"{report_summary.get('status')} · {report_summary.get('totalRows', 0)} 条记录 · 同步到 {' / '.join(report_summary.get('affectedModules') or ['总览'])}",
        "taskHint": f"当前可见 {len(active_tasks)} 个任务",
        "updatedModules": report_summary.get("affectedModules") or [],
        "latestSyncedAt": report_summary.get("latestSyncedAt"),
    }
    return {
        "mode": "today_task_workbench",
        "sections": DASHBOARD_WORKBENCH_SECTIONS,
        "todayPriorityTasks": priority_tasks,
        "highRiskItems": high_risk,
        "latestReportResult": report_result,
        "pendingReviewItems": review_items,
        "completionProgress": {
            "visibleActive": counters.get("visibleActive", len(active_tasks)),
            "processing": counters.get("processing", 0),
            "pendingReview": counters.get("reviewing", len(review_items)),
            "returned": counters.get("returned", 0),
            "completed": completed_count,
            "completionRate": completion_rate,
            "summary": f"已完成 {completed_count} 个，当前可见待办 {len(active_tasks)} 个",
        },
    }


def get_dashboard_summary(user_id: str | None = None) -> Dict[str, Any]:
    active_tasks = list_tasks(viewer_id=user_id, active_only=True)
    all_tasks = list_tasks(viewer_id=user_id, active_only=False)
    counters = get_task_counters_for_user(user_id)
    v3_summary = get_v3_dashboard_summary(user_id)
    projection = projection_summary(user_id)
    products = projected_products(user_id)
    reports = projected_report_groups(user_id)
    logs = list_logs()[:5]
    report_summary = _report_summary(reports, projection)
    has_data = bool(projection.get("hasData") or report_summary["importedCount"] or active_tasks or logs)
    task_queue = _task_queue(active_tasks)
    high_tasks = [task for task in active_tasks if _is_high_risk(task)]
    workbench = _dashboard_workbench(active_tasks, all_tasks, report_summary, counters)
    return {
        "apiEntry": "/api/modules/dashboard",
        "version": DASHBOARD_VERSION,
        "dashboardMode": "today_task_workbench",
        "workbenchSections": DASHBOARD_WORKBENCH_SECTIONS,
        "hasData": has_data,
        "emptyState": "暂无数据",
        "title": "今日任务台",
        "heroBadge": f"{len(workbench['todayPriorityTasks'])} 个优先任务" if has_data else "先上传报表",
        "latestImport": report_summary,
        "metrics": [
            {"label": "优先任务", "value": len(workbench["todayPriorityTasks"]), "desc": "今日先处理"},
            {"label": "高风险", "value": len(high_tasks), "desc": "需要关注"},
            {"label": "待复核", "value": workbench["completionProgress"]["pendingReview"], "desc": "等待确认"},
            {"label": "完成率", "value": f"{workbench['completionProgress']['completionRate']}%", "desc": "任务进度"},
        ],
        "taskQueue": task_queue,
        "tasks": active_tasks[:6],
        "todayWorkbench": workbench,
        "recentLogs": logs,
        "v3": v3_summary,
        "projection": projection,
        "productsCount": len(products),
    }
