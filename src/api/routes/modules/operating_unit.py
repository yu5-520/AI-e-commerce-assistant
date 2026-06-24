"""Operating unit route for productized store row tags and business judgment."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List

from fastapi import APIRouter, Request

from src.services.account_service import current_user, list_stores, user_id_from_headers
from src.services.module_projection_service import projection_summary, projected_products, projected_traffic
from src.services.module_task_service import get_task_counters_for_user
from src.services.report_alert_service import get_v3_dashboard_summary

router = APIRouter()


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value).replace(",", "").strip()))
    except (TypeError, ValueError):
        return default


def _percent(value: Any) -> float | None:
    if value in {None, "", "—"}:
        return None
    text = str(value).replace("%", "").strip()
    try:
        return float(text) / 100
    except (TypeError, ValueError):
        return None


def _store_count(products: List[Dict[str, Any]]) -> int:
    stores = {item.get("storeId") or item.get("store") for item in products if item.get("storeId") or item.get("store")}
    return len(stores) or (1 if products else 0)


def _store_weight_tag(products: List[Dict[str, Any]], traffic: List[Dict[str, Any]]) -> str:
    if len(products) >= 10 or len(traffic) >= 8:
        return "高权重店铺"
    if len(products) <= 2 and len(traffic) <= 1:
        return "测试店铺"
    return "常规店铺"


def _product_role(item: Dict[str, Any]) -> str:
    inventory_level = item.get("inventoryLevel")
    after_sales_level = item.get("afterSalesLevel")
    margin = _percent(item.get("grossMargin"))
    if after_sales_level in {"danger", "warning"}:
        return "售后风险款"
    if inventory_level in {"danger", "warning"}:
        return "库存风险款"
    if margin is not None and margin < 0.2:
        return "低毛利款"
    if item.get("orderSummary"):
        return "成交款"
    return "观察款"


def _risk_tags(products: List[Dict[str, Any]], active_alert_count: int = 0) -> List[str]:
    tags: List[str] = []
    if any(item.get("inventoryLevel") in {"danger", "warning"} for item in products):
        tags.append("库存风险")
    if any(item.get("afterSalesLevel") in {"danger", "warning"} for item in products):
        tags.append("售后风险")
    if any((_percent(item.get("grossMargin")) or 1) < 0.2 for item in products):
        tags.append("低毛利风险")
    if active_alert_count > 0:
        tags.append("经营预警")
    return tags or ["常规观察"]


def _tag_level(value: str) -> str:
    if any(word in value for word in ["风险", "强处理", "低毛利", "库存"]):
        return "warning"
    if any(word in value for word in ["高权重", "成交", "稳定"]):
        return "good"
    return "watch"


def _main_risk(risk_tags: List[str]) -> str:
    for risk in ["库存风险", "低毛利风险", "售后风险", "经营预警"]:
        if risk in risk_tags:
            return risk
    return risk_tags[0] if risk_tags else "常规观察"


def _visible_store_rows(user: Dict[str, Any], products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    store_ids = list(user.get("storeIds") or [])
    product_store_ids = [str(item.get("storeId")) for item in products if item.get("storeId")]
    for store_id in product_store_ids:
        if store_id not in store_ids:
            store_ids.append(store_id)
    store_map = {store["id"]: store for store in list_stores()}
    rows: List[Dict[str, Any]] = []
    for index, store_id in enumerate(store_ids, start=1):
        store = store_map.get(store_id) or {"id": store_id, "name": store_id or f"店铺 {index}", "platform": "导入数据"}
        rows.append({"storeId": store.get("id"), "storeName": store.get("name") or store_id or f"店铺 {index}", "platform": store.get("platform") or "导入数据"})
    if not rows and products:
        rows.append({"storeId": "GLOBAL", "storeName": "未绑定店铺", "platform": "导入数据"})
    return rows


def build_store_rows(products: List[Dict[str, Any]], traffic: List[Dict[str, Any]], user: Dict[str, Any], task_counters: Dict[str, Any]) -> List[Dict[str, Any]]:
    products_by_store: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    traffic_by_store: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in products:
        products_by_store[str(item.get("storeId") or "GLOBAL")].append(item)
    for item in traffic:
        traffic_by_store[str(item.get("storeId") or "GLOBAL")].append(item)
    rows: List[Dict[str, Any]] = []
    for store in _visible_store_rows(user, products):
        store_id = str(store.get("storeId") or "GLOBAL")
        store_products = products_by_store.get(store_id, [])
        store_traffic = traffic_by_store.get(store_id, [])
        role_counter = Counter(_product_role(item) for item in store_products)
        product_role_tags = [f"{name} {count}" for name, count in role_counter.most_common()] or ["暂无商品"]
        risk_tags = _risk_tags(store_products)
        risk_count = 0 if risk_tags == ["常规观察"] else len(risk_tags)
        task_intensity = "强处理" if risk_count or len(store_products) >= 8 else "常规处理"
        store_weight = _store_weight_tag(store_products, store_traffic)
        main_risk = _main_risk(risk_tags)
        rows.append({
            "storeId": store.get("storeId"),
            "storeName": store.get("storeName"),
            "platform": store.get("platform"),
            "storeWeightTag": store_weight,
            "productCount": len(store_products),
            "trafficCount": len(store_traffic),
            "productRoleTags": product_role_tags[:4],
            "riskTags": risk_tags[:4],
            "taskIntensity": task_intensity,
            "activeTaskCount": 0,
            "alertCount": risk_count,
            "level": _tag_level(task_intensity if task_intensity == "强处理" else main_risk),
            "judgment": f"{main_risk} · {task_intensity}",
        })
    return rows


def build_operating_judgment(store_rows: List[Dict[str, Any]], task_counters: Dict[str, Any]) -> Dict[str, Any]:
    strong_count = sum(1 for row in store_rows if row.get("taskIntensity") == "强处理")
    risk_rows = [row for row in store_rows if "常规观察" not in (row.get("riskTags") or [])]
    main_risk = (risk_rows[0].get("riskTags") or ["常规观察"])[0] if risk_rows else "常规观察"
    active_tasks = _as_int(task_counters.get("visibleActive"), 0)
    if strong_count:
        summary = f"当前 {len(store_rows)} 个店铺中，{strong_count} 个需要强处理，优先处理{main_risk}店铺。"
    else:
        summary = f"当前 {len(store_rows)} 个店铺以常规观察为主，保持同步并等待下一轮数据。"
    return {"title": "经营判断", "summary": summary, "priority": "按店铺逐行处理", "mainRisk": main_risk, "strongStoreCount": strong_count, "activeTaskCount": active_tasks}


@router.get("/operating-unit")
def operating_unit(request: Request) -> Dict[str, Any]:
    user_id = user_id_from_headers(request.headers)
    user = current_user(user_id)
    projection = projection_summary(user_id)
    v3 = get_v3_dashboard_summary(user_id)
    products = projected_products(user_id)
    traffic = projected_traffic(user_id)
    task_counters = get_task_counters_for_user(user_id)
    store_rows = build_store_rows(products, traffic, user, task_counters)
    risk_store_count = sum(1 for row in store_rows if "常规观察" not in (row.get("riskTags") or []))
    active_tasks = _as_int(task_counters.get("visibleActive"), 0)
    has_data = bool(projection.get("hasData") or v3.get("latestDataVersion") or products or traffic or store_rows)
    if not has_data:
        return {
            "version": "5.2.0",
            "hasData": False,
            "emptyState": "暂无数据",
            "syncState": {"label": "等待数据", "status": "empty"},
            "viewer": {"id": user.get("id"), "roleId": user.get("roleId"), "roleName": user.get("roleName")},
            "metrics": [],
            "storeRows": [],
            "operatingJudgment": None,
            "tasks": task_counters,
        }
    return {
        "version": "5.2.0",
        "hasData": True,
        "unitName": "经营单元",
        "syncState": {"label": "数据已同步", "status": "synced", "latestDataVersion": projection.get("latestDataVersion") or v3.get("latestDataVersion")},
        "latestSnapshotAt": projection.get("latestSnapshotAt") or v3.get("latestSnapshotAt"),
        "viewer": {"id": user.get("id"), "roleId": user.get("roleId"), "roleName": user.get("roleName")},
        "metrics": [
            {"label": "店铺", "value": len(store_rows)},
            {"label": "商品", "value": len(products)},
            {"label": "风险店铺", "value": risk_store_count},
            {"label": "任务", "value": active_tasks},
        ],
        "storeRows": store_rows,
        "operatingJudgment": build_operating_judgment(store_rows, task_counters),
        "tasks": task_counters,
        "projection": projection,
        "v3": v3,
    }
