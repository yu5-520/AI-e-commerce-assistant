"""Product module routes."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

from src.api.routes.modules.common import find_or_404
from src.services.module_data_service import PRODUCTS
from src.services.module_task_service import create_task, visible_candidates

router = APIRouter()


def product_task_payload(item: Dict[str, Any]) -> Dict[str, Any]:
    risk_domain = "售后" if item["afterSalesLevel"] != "good" else "库存" if item["inventoryLevel"] == "danger" else "商品"
    high_risk = item["afterSalesLevel"] != "good" or item["inventoryLevel"] == "danger"
    return {
        "entityType": "商品",
        "entityId": item["id"],
        "riskDomain": risk_domain,
        "actionType": "观察" if risk_domain == "商品" else "复查",
        "sourceModule": "商品经营列表",
        "source": "商品触发",
        "sourceRoute": "business-products",
        "productId": item["id"],
        "imageLabel": item["imageLabel"],
        "productShort": item["shortName"],
        "productTitle": item["title"],
        "title": item["title"],
        "platform": item["platform"],
        "store": item["store"],
        "link": item["link"],
        "priority": "高" if high_risk else "中",
        "priorityLevel": "danger" if high_risk else "warning",
        "deadline": "今天内" if high_risk else "明天前",
        "taskType": "售后复查" if item["afterSalesLevel"] != "good" else "库存承接" if item["inventoryLevel"] == "danger" else "商品优化",
        "taskSignal": "先查售后" if item["afterSalesLevel"] != "good" else "确认补货" if item["inventoryLevel"] == "danger" else "优化测试",
        "task": "复查售后原因，暂不扩大推广" if item["afterSalesLevel"] != "good" else "确认补货周期，再决定活动节奏" if item["inventoryLevel"] == "danger" else "加入商品优化观察",
        "reason": item["suggestion"],
        "judgmentTags": [item["inventoryStatus"], item["afterSales"], f"毛利 {item['grossMargin']}"],
    }


@router.get("/product")
def product() -> List[Dict[str, Any]]:
    return visible_candidates(PRODUCTS, product_task_payload)


@router.post("/product/{product_id}/tasks")
def product_task(product_id: str) -> Dict[str, Any]:
    item = find_or_404(PRODUCTS, product_id, "product")
    return create_task(product_task_payload(item))
