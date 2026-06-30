"""Product module routes backed by V14.8 frontend read model."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query, Request

from src.services.account_service import user_id_from_headers
from src.services.frontend_read_model_service import FRONTEND_READ_MODEL_VERSION, read_product_detail, read_product_views
from src.services.task_pool_station_service import enter_task_pool_from_snapshot
from src.services.task_snapshot_station_service import create_task_snapshot

router = APIRouter()
PRODUCT_ARCHIVE_VERSION = "14.8.0"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_archive_item(item: Dict[str, Any]) -> Dict[str, Any]:
    product_id = _text(item.get("productId") or item.get("id") or item.get("bundleId")) or "PRODUCT"
    store_id = _text(item.get("storeId") or "GLOBAL") or "GLOBAL"
    archive_id = f"{store_id}::{product_id}"
    metrics = item.get("metrics") if isinstance(item.get("metrics"), dict) else {}
    normalized = {
        **item,
        "id": archive_id,
        "objectId": archive_id,
        "archiveId": archive_id,
        "productId": product_id,
        "rawProductId": product_id,
        "storeId": store_id,
        "storeName": item.get("storeName") or store_id,
        "store": item.get("storeName") or store_id,
        "title": item.get("title") or product_id,
        "shortName": item.get("title") or product_id,
        "inventory": metrics.get("inventory"),
        "paymentAmount": metrics.get("paymentAmount"),
        "roas": metrics.get("roas") or metrics.get("roi"),
        "refundRate": metrics.get("refundRate"),
        "grossMargin": metrics.get("grossMargin"),
        "productArchiveVersion": PRODUCT_ARCHIVE_VERSION,
        "readModelVersion": FRONTEND_READ_MODEL_VERSION,
        "sourceRoute": "business-products",
        "readMode": "frontend_product_view_only",
    }
    return normalized


def product_items(user_id: str | None, store_id: str | None = None, store_name: str | None = None) -> List[Dict[str, Any]]:
    result = read_product_views(store_id=store_id, limit=500)
    items = [_normalize_archive_item(item) for item in result.get("items") or []]
    if store_name:
        wanted = _text(store_name)
        items = [item for item in items if wanted in {_text(item.get("storeName")), _text(item.get("store"))}]
    return items


def product_task_payload(item: Dict[str, Any]) -> Dict[str, Any]:
    metrics = item.get("metrics") if isinstance(item.get("metrics"), dict) else {}
    strength = item.get("signalStrength") or "low"
    priority = "高" if strength == "high" else "中" if strength == "medium" else "低"
    return {"entityType": "商品", "entityId": item["id"], "riskDomain": item.get("metricCode") or "商品", "actionType": "manual_product_review", "sourceModule": "商品模块", "source": "前端读模型人工请求", "sourceRoute": "business-products", "productId": item.get("productId") or item["id"], "objectId": item["id"], "storeIds": [item.get("storeId")] if item.get("storeId") else [], "visibleStoreIds": [item.get("storeId")] if item.get("storeId") else [], "imageLabel": item.get("imageLabel") or "品", "productShort": item.get("shortName") or item.get("title") or item.get("productId") or item["id"], "productTitle": item.get("title") or item.get("productId") or item["id"], "title": item.get("title") or item.get("productId") or item["id"], "platform": item.get("platform") or "导入数据", "store": item.get("storeName") or item.get("store") or "未绑定店铺", "priority": priority, "priorityLevel": "danger" if priority == "高" else "warning" if priority == "中" else "good", "deadline": "今天内" if priority == "高" else "明天前", "taskType": "商品经营复核", "taskSignal": item.get("primarySignalType") or "前端人工请求", "task": "基于商品全量包读模型复核商品状态，提交截图、数据口径和处理结论。", "reason": "商品来自 frontend_product_view；页面请求不触发商品投影或Agent重算。", "judgmentTags": [item.get("verticalCategory", "未归类"), f"支付 {metrics.get('paymentAmount', '—')}", f"退款率 {metrics.get('refundRate', '—')}", f"库存 {metrics.get('inventory', '—')}"], "sourceDataVersions": [item.get("dataVersion")] if item.get("dataVersion") else [], "sourceDatasets": ["frontend_product_view"]}


def _enter_snapshot_pool(payload: Dict[str, Any], user_id: str | None = None) -> Dict[str, Any]:
    entity_id = payload.get("entityId") or payload.get("productId")
    source_version = (payload.get("sourceDataVersions") or [None])[0]
    priority = payload.get("priority") or "中"
    decision = "manager_review_required" if priority == "高" else "create_task_snapshot"
    task_plan = {"title": payload.get("title") or entity_id, "subtitle": "manual_product_read_model_request_v14_8", "entityType": payload.get("entityType") or "商品", "entityId": entity_id, "taskType": payload.get("taskType") or "商品复核", "actionType": payload.get("actionType") or "manual_request", "priority": priority, "deadline": payload.get("deadline") or "24小时内", "riskDomain": payload.get("riskDomain") or "商品", "sopSteps": [payload.get("task") or "复核该经营对象。", "提交处理截图、数据口径和影响范围。", "后续由系统复盘相关指标。"], "evidenceRequirements": ["页面来源", "处理截图", "数据口径"], "reviewMetrics": ["支付金额", "ROAS/ROI", "点击率", "转化率", "退款率", "库存"], "needManagerReview": decision == "manager_review_required", "reason": payload.get("reason") or payload.get("taskSignal")}
    snapshot = create_task_snapshot({"dataVersion": source_version, "decision": decision, "confidence": 0.7, "entityType": payload.get("entityType") or "商品", "entityId": entity_id, "signalRef": f"manual:product-read-model:{entity_id}:{source_version or 'latest'}", "ragContext": {"source": "product_read_model_manual_request", "version": PRODUCT_ARCHIVE_VERSION}, "agentJudgment": {"decision": decision, "confidence": 0.7, "reason": task_plan["reason"], "status": "manual_read_model_snapshot_bridge"}, "taskPlan": task_plan, "evidenceRequirements": task_plan["evidenceRequirements"], "systemFacts": {"modulePayload": payload}, "source": "product_module_read_model_manual_request"}, created_by=user_id)
    pool = enter_task_pool_from_snapshot(snapshot.get("taskSnapshotId"), created_by=user_id)
    return {"version": PRODUCT_ARCHIVE_VERSION, "mode": "manual_request_via_task_snapshot", "snapshot": snapshot, "pool": pool, "task": pool.get("task") if isinstance(pool, dict) else None}


@router.get("/product")
def product(request: Request, store_id: str | None = Query(None, alias="storeId"), store_name: str | None = Query(None, alias="storeName")) -> list[Dict[str, Any]]:
    user_id = user_id_from_headers(request.headers)
    return product_items(user_id, store_id=store_id, store_name=store_name)


@router.get("/product/{product_id}")
def product_detail(request: Request, product_id: str) -> Dict[str, Any]:
    cached = read_product_detail(product_id)
    if cached.get("item"):
        return _normalize_archive_item(cached["item"])
    for item in product_items(user_id_from_headers(request.headers)):
        if product_id in {item.get("id"), item.get("productId"), item.get("archiveId"), item.get("objectId")}:
            return item
    raise HTTPException(status_code=404, detail="product not found in frontend read model")


@router.post("/product/{product_id}/tasks")
def product_task(request: Request, product_id: str) -> Dict[str, Any]:
    user_id = user_id_from_headers(request.headers)
    item = product_detail(request, product_id)
    return _enter_snapshot_pool(product_task_payload(item), user_id=user_id)
