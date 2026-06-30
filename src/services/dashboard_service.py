"""V14.8 dashboard read-model service.

Dashboard is a pure frontend read path. It reads cached read-model tables and must
not rebuild operating snapshots, run projections, trigger Agent, or sync tasks.
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.services.frontend_read_model_service import FRONTEND_READ_MODEL_VERSION, read_dashboard_view, read_product_views, read_task_views

DASHBOARD_VERSION = "14.8.0"
DASHBOARD_WORKBENCH_SECTIONS = ["todayPriorityTasks", "highRiskItems", "latestReportResult", "pendingReviewItems", "completionProgress"]
DONE_STATUS = {"已完成", "已拒绝", "已确认", "已归档", "已通过", "已写入复盘"}


def _task_card(task: Dict[str, Any], rank: int) -> Dict[str, Any]:
    return {
        "rank": rank,
        "id": task.get("taskId") or task.get("id"),
        "title": task.get("title") or "经营任务",
        "subtitle": task.get("subtitle") or task.get("workflowStatus") or task.get("status") or "SOP任务",
        "productId": task.get("productId"),
        "riskDomain": task.get("riskDomain") or task.get("subtitle") or "经营",
        "priority": task.get("priority") or "中",
        "priorityLevel": "danger" if task.get("priority") == "高" else "warning" if task.get("priority") == "中" else "good",
        "deadline": task.get("deadline") or "本周内",
        "status": task.get("workflowStatus") or task.get("status") or "待处理",
        "source": "frontend_task_view",
        "assigneeName": task.get("assigneeName") or "未派发",
        "reviewerName": task.get("reviewerName") or "待复核人",
        "reason": task.get("subtitle") or "读模型任务",
        "route": "business-actions",
    }


def _active(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [task for task in tasks if task.get("status") not in DONE_STATUS]


def _dashboard_workbench(tasks: List[Dict[str, Any]], dashboard: Dict[str, Any]) -> Dict[str, Any]:
    active = _active(tasks)
    top = dashboard.get("topTasks") if isinstance(dashboard.get("topTasks"), list) else active[:5]
    priority_tasks = [_task_card(task, index) for index, task in enumerate(top[:5], start=1)]
    high_risk = [_task_card(task, index) for index, task in enumerate([task for task in active if task.get("priority") == "高"][:3], start=1)]
    review_items = [_task_card(task, index) for index, task in enumerate([task for task in active if task.get("managerApproval") or task.get("status") in {"待复核", "待拆分"}][:3], start=1)]
    completed_count = len([task for task in tasks if task.get("status") in DONE_STATUS])
    total_count = max(len(active) + completed_count, 1)
    counts = dashboard.get("counts") if isinstance(dashboard.get("counts"), dict) else {}
    return {
        "mode": "v14_8_frontend_read_model_dashboard",
        "sections": DASHBOARD_WORKBENCH_SECTIONS,
        "todayPriorityTasks": priority_tasks,
        "highRiskItems": high_risk,
        "pendingReviewItems": review_items,
        "emptyPriorityText": "当前无需要立即处理的高风险任务，低价值信号已沉淀为观察/证据/数据缺口。",
        "latestReportResult": {
            "label": "frontend_read_model",
            "status": "已同步" if dashboard.get("ready") else "待同步",
            "summary": "总览读取前端读模型，不触发快照重算、任务生成或Agent判断。",
            "taskHint": f"执行任务 {counts.get('activeTasks', len(active))} 个",
            "updatedModules": ["总览", "商品", "任务", "系统状态"],
            "latestSyncedAt": dashboard.get("cachedAt") or dashboard.get("updatedAt"),
        },
        "completionProgress": {
            "visibleActive": counts.get("activeTasks", len(active)),
            "processing": counts.get("processing", len([task for task in active if task.get("status") == "处理中"])),
            "pendingReview": counts.get("managerReview", len(review_items)),
            "returned": len([task for task in active if task.get("workflowStatus") == "已退回"]),
            "completed": completed_count,
            "completionRate": round(completed_count / total_count * 100),
            "summary": f"已完成 {completed_count} 个，当前执行任务 {counts.get('activeTasks', len(active))} 个",
        },
    }


def get_dashboard_summary(user_id: str | None = None) -> Dict[str, Any]:
    dashboard = read_dashboard_view()
    task_view = read_task_views(limit=200)
    product_view = read_product_views(limit=500)
    tasks = task_view.get("items") or []
    products = product_view.get("items") or []
    workbench = _dashboard_workbench(tasks, dashboard)
    counts = dashboard.get("counts") if isinstance(dashboard.get("counts"), dict) else {}
    has_data = bool(dashboard.get("ready") or tasks or products)
    return {
        "apiEntry": "/api/modules/dashboard",
        "canonicalReadModelEntry": "/api/view/dashboard",
        "version": DASHBOARD_VERSION,
        "readModelVersion": FRONTEND_READ_MODEL_VERSION,
        "dashboardMode": "v14_8_frontend_read_model_reader",
        "workbenchSections": DASHBOARD_WORKBENCH_SECTIONS,
        "hasData": has_data,
        "emptyState": "暂无数据",
        "title": "今日任务台",
        "heroBadge": f"{len(workbench['todayPriorityTasks'])} 个优先任务" if has_data else "等待读模型",
        "latestImport": workbench["latestReportResult"],
        "metrics": [
            {"label": "优先任务", "value": len(workbench["todayPriorityTasks"]), "desc": "今日先处理"},
            {"label": "高风险", "value": counts.get("highRiskProducts", 0), "desc": "读模型"},
            {"label": "店铺", "value": counts.get("stores", 0), "desc": "缓存读取"},
            {"label": "商品", "value": counts.get("products", len(products)), "desc": "缓存读取"},
        ],
        "taskQueue": workbench["todayPriorityTasks"],
        "tasks": tasks[:6],
        "todayWorkbench": workbench,
        "recentLogs": [],
        "snapshot": {"version": FRONTEND_READ_MODEL_VERSION, "readMode": "frontend_read_model_only", "snapshotKey": dashboard.get("cachedAt"), "pipelineGate": None},
        "objectSummary": {"productCount": counts.get("products", len(products)), "source": "frontend_product_view"},
        "productsCount": counts.get("products", len(products)),
        "forbiddenRuntimeStages": ["materialize_system_product_snapshot", "materialize_product_signal_snapshot", "generate_signal_pool", "run_agent_judgment_station", "sync_ready_task_snapshots", "projection_summary", "projected_products", "dataset_rows", "rag_retrieval", "llm_generation"],
        "rule": "V14.8：总览只读 frontend_dashboard_view/frontend_task_view/frontend_product_view；页面切换不触发任何计算链路。",
    }
