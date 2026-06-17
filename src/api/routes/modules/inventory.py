"""Inventory center routes."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Request

from src.api.routes.modules.common import find_or_404
from src.services.account_service import current_user, user_id_from_headers, visible_store_ids_for_user
from src.services.module_data_service import PRODUCTS
from src.services.module_task_service import create_task, visible_candidates
from src.services.report_alert_service import attach_alert_state

router = APIRouter()


def scoped_items(items: List[Dict[str, Any]], request: Request | None = None) -> List[Dict[str, Any]]:
    if request is None:
        return items
    user_id = user_id_from_headers(request.headers)
    user = current_user(user_id)
    if user.get("roleId") in {"owner", "manager", "finance"}:
        return items
    allowed = set(visible_store_ids_for_user(user_id))
    return [item for item in items if item.get("storeId") in allowed]


def inventory_status(item: Dict[str, Any]) -> str:
    level = item.get("inventoryLevel")
    if level == "danger":
        return "库存告急"
    if level == "warning":
        return item.get("inventoryStatus") or "库存关注"
    return "正常"


def inventory_payload(item: Dict[str, Any]) -> Dict[str, Any]:
    level = item.get("inventoryLevel") or "good"
    high_risk = level == "danger"
    return {
        "entityType": "库存",
        "entityId": item["id"],
        "riskDomain": "库存",
        "actionType": "复查" if level != "good" else "观察",
        "sourceModule": "库存中心",
        "source": "库存触发",
        "sourceRoute": "inventory-center",
        "productId": item["id"],
        "storeIds": [item.get("storeId")] if item.get("storeId") else [],
        "visibleStoreIds": [item.get("storeId")] if item.get("storeId") else [],
        "imageLabel": item.get("imageLabel"),
        "productShort": item.get("shortName"),
        "productTitle": item.get("title"),
        "title": f"库存复查｜{item.get('shortName') or item.get('title')}",
        "platform": item.get("platform"),
        "store": item.get("store"),
        "link": item.get("link"),
        "priority": "高" if high_risk else "中" if level == "warning" else "低",
        "priorityLevel": "danger" if high_risk else "warning" if level == "warning" else "good",
        "deadline": "今天内" if high_risk else "明天前",
        "taskType": "库存补货复核" if high_risk else "库存承接检查",
        "taskSignal": "确认补货" if high_risk else "确认安全库存",
        "task": "确认可售库存、安全库存和补货周期，再决定活动节奏。",
        "reason": item.get("suggestion") or item.get("inventoryStatus") or "库存需要复核。",
        "judgmentTags": [inventory_status(item), f"库存 {item.get('inventory')}", f"毛利 {item.get('grossMargin')}", item.get("store")],
    }


def inventory_card(item: Dict[str, Any]) -> Dict[str, Any]:
    return attach_alert_state({
        "id": item.get("id"),
        "storeId": item.get("storeId"),
        "productId": item.get("id"),
        "title": item.get("title"),
        "shortName": item.get("shortName"),
        "imageLabel": item.get("imageLabel"),
        "platform": item.get("platform"),
        "store": item.get("store"),
        "inventory": item.get("inventory"),
        "inventoryStatus": inventory_status(item),
        "inventoryLevel": item.get("inventoryLevel"),
        "price": item.get("price"),
        "grossMargin": item.get("grossMargin"),
        "suggestion": item.get("suggestion"),
        "sourceRoute": "inventory-center",
    }, "库存", item.get("id"))


@router.get("/inventory")
def inventory(request: Request) -> Dict[str, Any]:
    items = [inventory_card(item) for item in scoped_items(PRODUCTS, request)]
    danger = len([item for item in items if item.get("inventoryLevel") == "danger"])
    warning = len([item for item in items if item.get("inventoryLevel") == "warning"])
    return {
        "module": "库存中心",
        "version": "3.1.0",
        "metrics": {"skuCount": len(items), "danger": danger, "warning": warning, "normal": max(len(items) - danger - warning, 0)},
        "items": visible_candidates(items, lambda item: inventory_payload({**item, "suggestion": item.get("suggestion") or item.get("inventoryStatus")})),
        "rules": ["库存低于安全线进入补货复核", "库存偏低先确认补货周期再放量", "库存异常任务继承店铺负责人"],
    }


@router.post("/inventory/{product_id}/tasks")
def inventory_task(product_id: str) -> Dict[str, Any]:
    item = find_or_404(PRODUCTS, product_id, "inventory product")
    return create_task(inventory_payload(item))
