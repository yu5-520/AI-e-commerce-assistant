"""Product module routes with store-scoped archive support."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Query, Request

from src.api.routes.modules.common import find_or_404
from src.services.account_service import user_id_from_headers
from src.services.module_projection_service import projected_products
from src.services.module_task_service import create_task, visible_candidates
from src.services.operating_object_store_service import list_operating_products
from src.services.product_archive_detail_service import enrich_product_archive_detail
from src.services.report_alert_service import attach_alert_state

router = APIRouter()
PRODUCT_ARCHIVE_VERSION = "12.1.2"


def _has_value(value: Any) -> bool:
    if value is None or value == "" or value == "—":
        return False
    if isinstance(value, (list, tuple, set, dict)) and len(value) == 0:
        return False
    return True


def _text(value: Any) -> str:
    return str(value or "").strip()


def _merge_products(projected: List[Dict[str, Any]], master: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: Dict[str, Dict[str, Any]] = {}
    for item in [*master, *projected]:
        product_id = _text(item.get("productId") or item.get("id"))
        if not product_id:
            continue
        store_id = _text(item.get("storeId") or item.get("normalizedStoreId") or item.get("store") or item.get("storeName") or "GLOBAL")
        key = _text(item.get("objectId")) or f"{store_id}::{product_id}"
        if key not in seen:
            seen[key] = dict(item)
        else:
            seen[key].update({key2: value for key2, value in item.items() if _has_value(value)})
    return list(seen.values())


def _archive_id(item: Dict[str, Any]) -> str:
    product_id = _text(item.get("productId") or item.get("id") or item.get("skuId") or item.get("title")) or "PRODUCT"
    store_id = _text(item.get("storeId") or item.get("normalizedStoreId") or item.get("store") or item.get("storeName") or "GLOBAL") or "GLOBAL"
    return _text(item.get("objectId")) or f"{store_id}::{product_id}"


def _normalize_archive_item(item: Dict[str, Any]) -> Dict[str, Any]:
    product_id = _text(item.get("productId") or item.get("id") or item.get("skuId") or item.get("title")) or "PRODUCT"
    store_id = _text(item.get("storeId") or item.get("normalizedStoreId") or item.get("store") or item.get("storeName") or "GLOBAL") or "GLOBAL"
    store_name = _text(item.get("storeName") or item.get("store") or item.get("normalizedStoreName") or store_id) or "未绑定店铺"
    archive_id = _archive_id(item)
    normalized = dict(item)
    normalized.update({
        "id": archive_id,
        "objectId": archive_id,
        "archiveId": archive_id,
        "productId": product_id,
        "rawProductId": product_id,
        "storeId": store_id,
        "storeName": store_name,
        "store": store_name,
        "productArchiveVersion": PRODUCT_ARCHIVE_VERSION,
    })
    return normalized


def _matches_store(item: Dict[str, Any], store_id: str | None = None, store_name: str | None = None) -> bool:
    wanted_id = _text(store_id)
    wanted_name = _text(store_name)
    if not wanted_id and not wanted_name:
        return True
    ids = {_text(item.get("storeId")), _text(item.get("normalizedStoreId")), _text(item.get("rawStoreId"))}
    names = {_text(item.get("storeName")), _text(item.get("store")), _text(item.get("normalizedStoreName")), _text(item.get("rawStoreName"))}
    if wanted_id and wanted_id in ids:
        return True
    if wanted_name and wanted_name in names:
        return True
    return False


def product_items(user_id: str | None, store_id: str | None = None, store_name: str | None = None) -> List[Dict[str, Any]]:
    merged = _merge_products(projected_products(user_id), list_operating_products(user_id))
    scoped = [item for item in merged if _matches_store(item, store_id=store_id, store_name=store_name)]
    return [_normalize_archive_item(item) for item in scoped]


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
        "productId": item.get("productId") or item["id"],
        "objectId": item["id"],
        "storeIds": [store_id] if store_id else [],
        "visibleStoreIds": [store_id] if store_id else [],
        "imageLabel": item.get("imageLabel") or "品",
        "productShort": item.get("shortName") or item.get("title") or item.get("productId") or item["id"],
        "productTitle": item.get("title") or item.get("productId") or item["id"],
        "title": item.get("title") or item.get("productId") or item["id"],
        "platform": item.get("platform") or "导入数据",
        "store": item.get("storeName") or item.get("store") or "未绑定店铺",
        "link": item.get("link") or item.get("productLink") or "",
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


def _visible_enriched_products(user_id: str | None, store_id: str | None = None, store_name: str | None = None) -> List[Dict[str, Any]]:
    items = visible_candidates(product_items(user_id, store_id=store_id, store_name=store_name), product_task_payload)
    with_alerts = [with_alert_state(item, user_id) for item in items]
    return [enrich_product_archive_detail(item) for item in with_alerts]


@router.get("/product")
def product(request: Request, store_id: str | None = Query(None, alias="storeId"), store_name: str | None = Query(None, alias="storeName")) -> list[Dict[str, Any]]:
    user_id = user_id_from_headers(request.headers)
    return _visible_enriched_products(user_id, store_id=store_id, store_name=store_name)


@router.get("/product/{product_id}")
def product_detail(request: Request, product_id: str) -> Dict[str, Any]:
    user_id = user_id_from_headers(request.headers)
    item = find_or_404(_visible_enriched_products(user_id), product_id, "product")
    return item


@router.post("/product/{product_id}/tasks")
def product_task(request: Request, product_id: str) -> Dict[str, Any]:
    user_id = user_id_from_headers(request.headers)
    item = find_or_404(product_items(user_id), product_id, "product")
    return create_task(product_task_payload(item))
