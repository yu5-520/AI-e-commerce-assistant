"""Dashboard service for the V12.13.1 snapshot workbench.

The dashboard is a reader. It must not call report projection, product
projection, traffic projection, task generation, RAG or LLM when opened.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from src.services.module_task_service import DONE_STATUS, PRIORITY_RANK, list_logs, list_tasks
from src.services.operating_unit_snapshot_service import get_operating_unit_snapshot

DASHBOARD_VERSION = "12.13.1"
DEADLINE_RANK = {"今天内": 1, "今日": 1, "今日内": 1, "明天前": 2, "明天": 2, "48小时内": 3, "本周内": 4}
DASHBOARD_WORKBENCH_SECTIONS = ["todayPriorityTasks", "highRiskItems", "latestReportResult", "pendingReviewItems", "completionProgress"]
HIDDEN_QUEUE_TYPES = {"backend_tag", "store_product_tag", "observe_candidate", "candidate_only", "report_seed_only", "merged_duplicate"}


def _short_time(value: str | None) -> str:
    if not value:
        return "已同步"
    text = str(value)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).strftime("%m-%d %H:%M")
    except ValueError:
        return text[-5:] if len(text) > 5 else text


def _deadline_rank(task: Dict[str, Any]) -> int:
    text = str(task.get("deadline") or task.get("timeBucket") or "本周内")
    for key, rank in DEADLINE_RANK.items():
        if key in text:
            return rank
    return 9


def _is_front_task(task: Dict[str, Any]) -> bool:
    return task.get("displayState") != "backend_only" and task.get("queueType") not in HIDDEN_QUEUE_TYPES


def _task_card(task: Dict[str, Any], rank: int) -> Dict[str, Any]:
    card = task.get("taskCard") or {}
    detail = task.get("taskDetailReport") or {}
    ownership = task.get("ownership") or {}
    title = card.get("title") or task.get("productTitle") or task.get("productId") or task.get("entityId") or task.get("title") or "经营任务"
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


def _dashboard_workbench(active_tasks: List[Dict[str, Any]], all_tasks: List[Dict[str, Any]], report_summary: Dict[str, Any]) -> Dict[str, Any]:
    front_tasks = [task for task in active_tasks if _is_front_task(task)]
    priority_tasks = _task_queue(front_tasks, limit=5)
    high_risk = _task_queue([task for task in front_tasks if _is_high_risk(task)], limit=3)
    review_items = _task_queue([task for task in front_tasks if _is_review_task(task)], limit=3)
    completed_count = len([task for task in all_tasks if task.get("status") in DONE_STATUS])
    total_count = max(completed_count + len(front_tasks), 1)
    completion_rate = round(completed_count / total_count * 100)
    report_result = {
        "label": report_summary.get("label"),
        "status": report_summary.get("status"),
        "summary": report_summary.get("userSummary") or "经营数据快照已同步。",
        "taskHint": f"执行任务 {len(front_tasks)} 个",
        "updatedModules": report_summary.get("affectedModules") or [],
        "latestSyncedAt": report_summary.get("latestSyncedAt"),
    }
    return {
        "mode": "v12_13_1_snapshot_dashboard_workbench",
        "sections": DASHBOARD_WORKBENCH_SECTIONS,
        "todayPriorityTasks": priority_tasks,
        "highRiskItems": high_risk,
        "pendingReviewItems": review_items,
        "emptyPriorityText": "当前无需要立即处理的高风险任务，低风险信号已沉淀为商品 / 店铺标签。",
        "latestReportResult": report_result,
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


def _snapshot_report_summary(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    sync = snapshot.get("syncState") or {}
    latest = sync.get("latestDataVersion") or (snapshot.get("objectStore") or {}).get("latestDataVersion")
    return {
        "label": latest or "经营快照",
        "status": "已同步" if snapshot.get("hasData") else "待同步",
        "rows": 0,
        "totalRows": 0,
        "importedCount": 1 if snapshot.get("hasData") else 0,
        "affectedModules": ["总览", "经营", "数据", "任务"] if snapshot.get("hasData") else [],
        "latestSyncedAt": _short_time(snapshot.get("latestSnapshotAt")),
        "technicalDataVersion": latest,
        "technicalDatasetName": "operating_unit_snapshot",
        "userSummary": "总览读取经营页快照，不再触发报表投影或商品重算。" if snapshot.get("hasData") else "等待报表同步。",
    }


def _metric_value(snapshot: Dict[str, Any], label: str, default: int = 0) -> int:
    for item in snapshot.get("metrics") or []:
        if item.get("label") == label:
            try:
                return int(item.get("value") or 0)
            except (TypeError, ValueError):
                return default
    return default


def get_dashboard_summary(user_id: str | None = None) -> Dict[str, Any]:
    snapshot = get_operating_unit_snapshot(user_id=user_id, allow_build=True)
    active_tasks = list_tasks(viewer_id=user_id, active_only=True)
    all_tasks = list_tasks(viewer_id=user_id, active_only=False)
    logs = list_logs()[:5]
    report_summary = _snapshot_report_summary(snapshot)
    workbench = _dashboard_workbench(active_tasks, all_tasks, report_summary)
    front_tasks = [task for task in active_tasks if _is_front_task(task)]
    high_tasks = [task for task in front_tasks if _is_high_risk(task)]
    product_count = _metric_value(snapshot, "商品", (snapshot.get("objectStore") or {}).get("productCount") or 0)
    store_count = _metric_value(snapshot, "店铺", (snapshot.get("objectStore") or {}).get("storeCount") or 0)
    has_data = bool(snapshot.get("hasData") or front_tasks or logs)
    return {
        "apiEntry": "/api/modules/dashboard",
        "version": DASHBOARD_VERSION,
        "dashboardMode": "v12_13_1_snapshot_reader",
        "workbenchSections": DASHBOARD_WORKBENCH_SECTIONS,
        "hasData": has_data,
        "emptyState": "暂无数据",
        "title": "今日任务台",
        "heroBadge": f"{len(workbench['todayPriorityTasks'])} 个优先任务" if has_data else "先上传报表",
        "latestImport": report_summary,
        "metrics": [
            {"label": "优先任务", "value": len(workbench["todayPriorityTasks"]), "desc": "今日先处理"},
            {"label": "高风险", "value": len(high_tasks), "desc": "执行队列"},
            {"label": "店铺", "value": store_count, "desc": "快照读取"},
            {"label": "商品", "value": product_count, "desc": "快照读取"},
        ],
        "taskQueue": workbench["todayPriorityTasks"],
        "tasks": front_tasks[:6],
        "todayWorkbench": workbench,
        "recentLogs": logs,
        "snapshot": {"version": snapshot.get("version"), "readMode": "snapshot_only", "snapshotKey": snapshot.get("snapshotKey"), "pipelineGate": snapshot.get("pipelineGate")},
        "objectSummary": snapshot.get("objectStore") or {},
        "productsCount": product_count,
        "forbiddenRuntimeStages": ["projection_summary", "projected_products", "projected_report_groups", "projected_traffic", "dataset_rows", "rag_retrieval", "llm_generation"],
        "rule": "V12.13.1：总览只读经营快照和轻量任务摘要，不再执行旧投影重算。",
    }
