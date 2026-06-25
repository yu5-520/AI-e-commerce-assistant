"""Dashboard service for the V11.8 productized task workbench."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from src.services.module_projection_service import DATASET_LABELS, projection_summary, projected_products, projected_report_groups
from src.services.module_task_service import DONE_STATUS, PRIORITY_RANK, get_task_counters_for_user, list_logs, list_tasks
from src.services.operating_object_store_service import operating_object_summary
from src.services.report_alert_service import get_v3_dashboard_summary

DASHBOARD_VERSION = "11.8.0"
DEADLINE_RANK = {"今天内": 1, "今日": 1, "今日内": 1, "明天前": 2, "明天": 2, "48小时内": 3, "本周内": 4}
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


def _is_front_task(task: Dict[str, Any]) -> bool:
    return task.get("displayState") != "backend_only" and task.get("queueType") not in {"backend_tag", "store_product_tag", "observe_candidate"}


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
    synced = bool(imported or projection.get("latestDataVersion"))
    return {
        "label": latest_report.get("name") if latest_report else latest_label,
        "status": "已同步" if synced else "待同步",
        "rows": _count_value(latest_report.get("count")) if latest_report else 0,
        "totalRows": total_rows,
        "importedCount": len(imported),
        "affectedModules": ["总览", "经营", "数据", "任务队列"] if synced else [],
        "latestSyncedAt": _short_time(projection.get("latestSnapshotAt")),
        "technicalDataVersion": projection.get("latestDataVersion"),
        "technicalDatasetName": latest_dataset,
        "userSummary": "经营数据、商品、店铺、标签和任务队列已同步。" if synced else "等待报表同步。",
    }


def _task_card(task: Dict[str, Any], rank: int) -> Dict[str, Any]:
    card = task.get("taskCard") or {}
    detail = task.get("taskDetailReport") or {}
    ownership = task.get("ownership") or {}
    title = card.get("title") or task.get("productId") or task.get("entityId") or task.get("title") or "经营任务"
    subtitle = card.get("subtitle") or detail.get("warningSummary") or task.get("riskDomain") or "SOP任务"
    return {
        "rank": rank,
        "id": task.get("id"),
        "title": title,
        "subtitle": subtitle,
        "productId": task.get("productId") or task.get("entityId"),
        "riskDomain": task.get("riskDomain") or subtitle,
        "priority": task.get("priority") or card.get("priority") or "中",
        "priorityLevel": task.get("priorityLevel") or "warning",
        "deadline": task.get("deadline") or card.get("deadline") or "本周内",
        "status": task.get("workflowStatus") or task.get("status") or "待处理",
        "source": task.get("source") or task.get("sourceModule") or "SOP任务包",
        "assigneeName": task.get("assigneeName") or ownership.get("assignedOperatorId") or "未派发",
        "reviewerName": task.get("reviewerName") or "待复核人",
        "reason": subtitle,
        "route": "business-actions",
    }


def _task_queue(tasks: List[Dict[str, Any]], limit: int = 6) -> List[Dict[str, Any]]:
    front_tasks = [task for task in tasks if _is_front_task(task)]
    sorted_tasks = sorted(front_tasks, key=lambda task: (PRIORITY_RANK.get(task.get("priority"), 9), _deadline_rank(task), task.get("manualOrder", 999999999), task.get("createdAt", "")))
    return [_task_card(task, index) for index, task in enumerate(sorted_tasks[:limit], start=1)]


def _is_high_risk(task: Dict[str, Any]) -> bool:
    return _is_front_task(task) and (task.get("priority") == "高" or task.get("priorityLevel") == "danger" or "高风险" in " ".join(task.get("judgmentTags") or []))


def _is_review_task(task: Dict[str, Any]) -> bool:
    return _is_front_task(task) and (task.get("status") in {"待复核", "已提交"} or task.get("workflowStatus") in {"待复核", "已提交"})


def _dashboard_workbench(active_tasks: List[Dict[str, Any]], all_tasks: List[Dict[str, Any]], report_summary: Dict[str, Any], counters: Dict[str, Any]) -> Dict[str, Any]:
    front_tasks = [task for task in active_tasks if _is_front_task(task)]
    priority_tasks = _task_queue(front_tasks, limit=5)
    high_risk = _task_queue([task for task in front_tasks if _is_high_risk(task)], limit=3)
    review_items = _task_queue([task for task in front_tasks if _is_review_task(task)], limit=3)
    completed_count = len([task for task in all_tasks if task.get("status") in DONE_STATUS])
    total_count = max(completed_count + len(front_tasks), 1)
    completion_rate = round(completed_count / total_count * 100)
    no_task_text = "当前无需要立即处理的高风险任务，低风险信号已沉淀为商品 / 店铺标签。"
    report_result = {
        "label": report_summary.get("label"),
        "status": report_summary.get("status"),
        "summary": report_summary.get("userSummary") or "经营数据已同步。",
        "taskHint": f"执行任务 {len(front_tasks)} 个",
        "updatedModules": report_summary.get("affectedModules") or [],
        "latestSyncedAt": report_summary.get("latestSyncedAt"),
    }
    return {
        "mode": "v11_8_today_task_workbench",
        "sections": DASHBOARD_WORKBENCH_SECTIONS,
        "todayPriorityTasks": priority_tasks,
        "highRiskItems": high_risk,
        "latestReportResult": report_result,
        "pendingReviewItems": review_items,
        "emptyPriorityText": no_task_text,
        "completionProgress": {
            "visibleActive": len(front_tasks),
            "processing": len([task for task in front_tasks if task.get("status") == "处理中"]),
            "pendingReview": len(review_items),
            "returned": len([task for task in front_tasks if task.get("workflowStatus") == "已退回"]),
            "completed": completed_count,
            "completionRate": completion_rate,
            "summary": f"已完成 {completed_count} 个，当前执行任务 {len(front_tasks)} 个",
        },
    }


def get_dashboard_summary(user_id: str | None = None) -> Dict[str, Any]:
    active_tasks = list_tasks(viewer_id=user_id, active_only=True)
    all_tasks = list_tasks(viewer_id=user_id, active_only=False)
    counters = get_task_counters_for_user(user_id)
    v3_summary = get_v3_dashboard_summary(user_id)
    projection = projection_summary(user_id)
    object_summary = operating_object_summary(user_id)
    products = projected_products(user_id)
    reports = projected_report_groups(user_id)
    logs = list_logs()[:5]
    report_summary = _report_summary(reports, projection)
    has_data = bool(projection.get("hasData") or object_summary.get("productCount") or object_summary.get("storeCount") or report_summary["importedCount"] or active_tasks or logs or products)
    workbench = _dashboard_workbench(active_tasks, all_tasks, report_summary, counters)
    front_tasks = [task for task in active_tasks if _is_front_task(task)]
    high_tasks = [task for task in front_tasks if _is_high_risk(task)]
    return {
        "apiEntry": "/api/modules/dashboard",
        "version": DASHBOARD_VERSION,
        "dashboardMode": "v11_8_today_task_workbench",
        "workbenchSections": DASHBOARD_WORKBENCH_SECTIONS,
        "hasData": has_data,
        "emptyState": "暂无数据",
        "title": "今日任务台",
        "heroBadge": f"{len(workbench['todayPriorityTasks'])} 个优先任务" if has_data else "先上传报表",
        "latestImport": report_summary,
        "metrics": [
            {"label": "优先任务", "value": len(workbench["todayPriorityTasks"]), "desc": "今日先处理"},
            {"label": "高风险", "value": len(high_tasks), "desc": "执行队列"},
            {"label": "店铺", "value": object_summary.get("storeCount") or 0, "desc": "经营对象"},
            {"label": "商品", "value": object_summary.get("productCount") or len(products), "desc": "已入库"},
        ],
        "taskQueue": workbench["todayPriorityTasks"],
        "tasks": front_tasks[:6],
        "todayWorkbench": workbench,
        "recentLogs": logs,
        "v3": v3_summary,
        "projection": projection,
        "objectSummary": object_summary,
        "productsCount": object_summary.get("productCount") or len(products),
        "rule": "V11.8 总览只展示任务摘要；完整 SOP 在详情页。",
    }
