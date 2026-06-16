"""Listing module routes."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

from src.api.routes.modules.common import find_or_404
from src.services.module_data_service import LISTINGS, clone
from src.services.module_task_service import create_task

router = APIRouter()


@router.get("/listing")
def listing() -> List[Dict[str, Any]]:
    return clone(LISTINGS)


@router.post("/listing/{listing_id}/tasks")
def listing_task(listing_id: str) -> Dict[str, Any]:
    item = find_or_404(LISTINGS, listing_id, "listing")
    return create_task({
        "entityType": "竞品机会" if item["mode"] == "competitor" else "商品",
        "entityId": item["id"],
        "riskDomain": "上新",
        "actionType": "复盘" if "复盘" in item["testType"] else "测试",
        "sourceModule": "上新测试台",
        "source": "上新触发",
        "sourceRoute": "business-listing",
        "productId": item["id"],
        "imageLabel": item["imageLabel"],
        "productShort": item["sourceName"],
        "productTitle": item["title"],
        "title": item["title"],
        "platform": item["platform"],
        "store": item["store"],
        "priority": "高" if item["statusLevel"] == "danger" else "中",
        "priorityLevel": item["statusLevel"],
        "deadline": item["due"],
        "taskType": item["testType"],
        "taskSignal": "确认测试版本",
        "task": f"{item['testType']}：{item['testPlan']}",
        "reason": f"{item['risk']} {item['suggestion']}",
        "judgmentTags": [item["sourceLabel"], item["testType"], item["targetMetric"]],
    })
