"""After-sales center routes."""

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


def aftersales_status(item: Dict[str, Any]) -> str:
    level = item.get("afterSalesLevel")
    if level == "danger":
        return "售后高危"
    if level == "warning":
        return item.get("afterSales") or "售后关注"
    return item.get("afterSales") or "正常"


def aftersales_payload(item: Dict[str, Any]) -> Dict[str, Any]:
    level = item.get("afterSalesLevel") or "good"
    high_risk = level in {"danger", "warning"}
    return {
        "entityType": "售后",
        "entityId": item["id"],
        "riskDomain": "售后",
        "actionType": "复查" if high_risk else "观察",
        "sourceModule": "售后中心",
        "source": "售后触发",
        "sourceRoute": "aftersales-center",
        "productId": item["id"],
        "storeIds": [item.get("storeId")] if item.get("storeId") else [],
        "visibleStoreIds": [item.get("storeId")] if item.get("storeId") else [],
        "imageLabel": item.get("imageLabel"),
        "productShort": item.get("shortName"),
        "productTitle": item.get("title"),
        "title": f"售后复查｜{item.get('shortName') or item.get('title')}",
        "platform": item.get("platform"),
        "store": item.get("store"),
        "link": item.get("link"),
        "priority": "高" if high_risk else "低",
        "priorityLevel": "danger" if high_risk else "good",
        "deadline": "今天内" if high_risk else "本周内",
        "taskType": "售后归因复查" if high_risk else "售后观察",
        "taskSignal": "先查售后" if high_risk else "保持观察",
        "task": "复查退款原因、详情页承诺和客服话术，售后归因完成前不继续放量。",
        "reason": item.get("suggestion") or item.get("afterSales") or "售后需要复核。",
        "judgmentTags": [aftersales_status(item), item.get("inventoryStatus"), f"毛利 {item.get('grossMargin')}", item.get("store")],
    }


def aftersales_card(item: Dict[str, Any]) -> Dict[str, Any]:
    return attach_alert_state({
        "id": item.get("id"),
        "storeId": item.get("storeId"),
        "productId": item.get("id"),
        "title": item.get("title"),
        "shortName": item.get("shortName"),
        "imageLabel": item.get("imageLabel"),
        "platform": item.get("platform"),
        "store": item.get("store"),
        "afterSales": aftersales_status(item),
        "afterSalesLevel": item.get("afterSalesLevel"),
        "inventoryStatus": item.get("inventoryStatus"),
        "refundFocus": "材质 / 尺寸 / 安装 / 物流 / 客服承诺",
        "grossMargin": item.get("grossMargin"),
        "suggestion": item.get("suggestion"),
        "sourceRoute": "aftersales-center",
    }, "售后", item.get("id"))


@router.get("/aftersales")
def aftersales(request: Request) -> Dict[str, Any]:
    items = [aftersales_card(item) for item in scoped_items(PRODUCTS, request)]
    abnormal = len([item for item in items if item.get("afterSalesLevel") != "good"])
    sensitive = len([item for item in items if item.get("afterSalesLevel") == "warning"])
    return {
        "module": "售后中心",
        "version": "3.1.0",
        "metrics": {"productCount": len(items), "abnormal": abnormal, "sensitive": sensitive, "normal": max(len(items) - abnormal, 0)},
        "items": visible_candidates(items, lambda item: aftersales_payload({**item, "suggestion": item.get("suggestion") or item.get("afterSales")})),
        "rules": ["退款偏高进入售后归因", "材质/尺寸/安装/客服承诺分开判断", "售后任务继承店铺负责人"],
    }


@router.post("/aftersales/{product_id}/tasks")
def aftersales_task(product_id: str) -> Dict[str, Any]:
    item = find_or_404(PRODUCTS, product_id, "aftersales product")
    return create_task(aftersales_payload(item))
