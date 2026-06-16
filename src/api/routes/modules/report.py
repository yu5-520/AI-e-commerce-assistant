"""Report module routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from src.api.routes.modules.common import find_or_404
from src.services.module_data_service import REPORT_DETAILS, REPORT_GROUPS, all_reports, clone
from src.services.module_task_service import create_task

router = APIRouter()


@router.get("/report")
def report() -> Dict[str, Any]:
    return {"reportGroups": clone(REPORT_GROUPS), "reportDetails": clone(REPORT_DETAILS)}


@router.get("/report/{report_id}")
def report_detail(report_id: str) -> Dict[str, Any]:
    if report_id not in REPORT_DETAILS:
        raise HTTPException(status_code=404, detail="report not found")
    return clone(REPORT_DETAILS[report_id])


@router.post("/report/{report_id}/tasks")
def report_task(report_id: str) -> Dict[str, Any]:
    item = find_or_404(all_reports(), report_id, "report")
    return create_task({
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
    })
