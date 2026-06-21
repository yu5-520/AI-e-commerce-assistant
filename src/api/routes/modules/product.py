"""Product module routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Request

from src.api.routes.modules.common import find_or_404
from src.services.account_service import user_id_from_headers
from src.services.module_projection_service import projected_products
from src.services.module_task_service import create_task, visible_candidates
from src.services.report_alert_service import attach_alert_state

router = APIRouter()


def product_task_payload(item: Dict[str, Any]) -> Dict[str, Any]:
    risk_domain = "售后" if item.get("afterSalesLevel") != "good" else "库存" if item.get("inventoryLevel") == "danger" else "商品"
    high_risk = item.get("afterSalesLevel") != "good" or item.get("inventoryLevel") == "danger"
    store_id = item.get("storeId")
    return {
        "entityType": "商品",
        "entityId": item["id"],
        "riskDomain": risk_domain,
        "actionType": "观察" if risk_domain == "商品" else "复查",
        "sourceModule": "商品模块",
        "source": "导入数据触发",
        "sourceRoute": "business-products",
        "productId": item["id"],
        "storeIds": [store_id] if store_id else [],
        "visibleStoreIds": [store_id] if store_id else [],
        "imageLabel": item.get("imageLabel") or "品",
        "productShort": item.get("shortName") or item["id"],
        "productTitle": item.get("title") or item["id"],
        "title": item.get("title") or item["id"],
        "platform": item.get("platform") or "导入数据",
        "store": item.get("store") or "未绑定店铺",
        "link": item.get("link") or "",
        "priority": "高" if high_risk else "中",
        "priorityLevel": "danger" if high_risk else "warning",
        "deadline": "今天内" if high_risk else "明天前",
        "taskType": "售后复查" if item.get("afterSalesLevel") != "good" else "库存承接" if item.get("inventoryLevel") == "danger" else "商品复核",
        "taskSignal": "先查售后" if item.get("afterSalesLevel") != "good" else "确认补货" if item.get("inventoryLevel") == "danger" else "数据复核",
        "task": item.get("suggestion") or "根据导入数据复核商品状态。",
        "reason": item.get("suggestion") or "商品内容来自报表导入后的模块投影。",
        "judgmentTags": [item.get("inventoryStatus", "库存待确认"), item.get("afterSales", "售后待确认"), f"毛利 {item.get('grossMargin', '—')}", *(item.get("sourceDataVersions") or [])[:1]],
        "sourceDataVersions": item.get("sourceDataVersions", []),
        "sourceDatasets": item.get("sourceDatasets", []),
    }


def with_alert_state(item: Dict[str, Any], user_id: str | None = None) -> Dict[str, Any]:
    return attach_alert_state(item, "商品", item["id"], user_id=user_id)


@router.get("/product")
def product(request: Request) -> list[Dict[str, Any]]:
    user_id = user_id_from_headers(request.headers)
    items = projected_products(user_id)
    return [with_alert_state(item, user_id) for item in visible_candidates(items, product_task_payload)]


@router.post("/product/{product_id}/tasks")
def product_task(request: Request, product_id: str) -> Dict[str, Any]:
    user_id = user_id_from_headers(request.headers)
    item = find_or_404(projected_products(user_id), product_id, "product")
    return create_task(product_task_payload(item))
