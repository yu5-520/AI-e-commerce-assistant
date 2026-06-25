"""Operating unit route for V11.10 object-store fail-closed verification."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List

from fastapi import APIRouter, Request

from src.services.account_service import current_user, list_stores, user_id_from_headers
from src.services.module_projection_service import projection_summary, projected_products, projected_traffic
from src.services.module_task_service import get_task_counters_for_user, list_tasks
from src.services.operating_object_store_service import list_operating_products, list_operating_stores, operating_object_summary
from src.services.report_alert_service import get_v3_dashboard_summary

router = APIRouter()
OPERATING_UNIT_VERSION = "11.10.0"


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


def _store_map() -> Dict[str, Dict[str, Any]]:
    stores: Dict[str, Dict[str, Any]] = {}
    for store in list_stores():
        stores[str(store.get("id"))] = store
        stores[str(store.get("name"))] = store
    return stores


def _clean_store_name(item: Dict[str, Any] | None, fallback: str = "未命名店铺") -> str:
    item = item or {}
    raw = str(item.get("storeName") or item.get("store") or "").strip()
    store_id = str(item.get("storeId") or item.get("id") or "").strip()
    if raw and raw not in {store_id, "导入数据店铺", "未绑定店铺", "GLOBAL", "未归属店铺"}:
        return raw
    store = _store_map().get(store_id)
    if store and store.get("name") and store.get("name") != store_id:
        return str(store["name"])
    return fallback if not store_id else fallback


def _store_platform(item: Dict[str, Any] | None, fallback: str = "平台") -> str:
    item = item or {}
    platform = str(item.get("platform") or "").strip()
    if platform and platform not in {"导入数据", "未知平台"}:
        return platform
    store_id = str(item.get("storeId") or item.get("id") or "").strip()
    store = _store_map().get(store_id)
    return str(store.get("platform") or fallback) if store else fallback


def _store_weight_tag(products: List[Dict[str, Any]], traffic: List[Dict[str, Any]]) -> str:
    if len(products) >= 10 or len(traffic) >= 8:
        return "高权重店铺"
    if len(products) <= 2 and len(traffic) <= 1:
        return "测试型店铺"
    return "中权重店铺"


def _product_role(item: Dict[str, Any]) -> str:
    inventory_level = item.get("inventoryLevel")
    after_sales_level = item.get("afterSalesLevel")
    margin = _percent(item.get("grossMargin"))
    if after_sales_level in {"danger", "warning"}:
        return "售后观察"
    if inventory_level in {"danger", "warning"}:
        return "库存观察"
    if margin is not None and margin < 0.2:
        return "低毛利观察"
    if item.get("orderSummary"):
        return "成交商品"
    if item.get("objectStoreVersion"):
        return "已入库商品"
    return "普通观察"


def _business_tags(products: List[Dict[str, Any]], active_alert_count: int = 0) -> List[str]:
    tags: List[str] = []
    if any(item.get("afterSalesLevel") in {"danger", "warning"} for item in products):
        tags.append("售后观察")
    if any(item.get("inventoryLevel") in {"danger", "warning"} for item in products):
        tags.append("库存观察")
    if any((_percent(item.get("grossMargin")) or 1) < 0.2 for item in products):
        tags.append("毛利观察")
    if any(item.get("objectStoreVersion") for item in products):
        tags.append("已入库")
    if active_alert_count > 0:
        tags.append("执行任务")
    return tags or ["常规观察"]


def _tag_level(value: str) -> str:
    if any(word in value for word in ["执行任务", "高风险", "库存"]):
        return "warning"
    if any(word in value for word in ["高权重", "成交", "稳定", "已入库"]):
        return "good"
    return "watch"


def _merge_products(projected: List[Dict[str, Any]], master: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: Dict[str, Dict[str, Any]] = {}
    for item in [*master, *projected]:
        product_id = str(item.get("id") or item.get("productId") or "").strip()
        if not product_id:
            continue
        store_id = str(item.get("storeId") or item.get("store") or item.get("storeName") or "GLOBAL").strip()
        key = f"{store_id}::{product_id}"
        if key not in seen:
            seen[key] = dict(item)
        else:
            seen[key].update({key2: value for key2, value in item.items() if value not in {None, "", "—"}})
    return list(seen.values())


def _visible_store_rows(products: List[Dict[str, Any]], traffic: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: Dict[str, Dict[str, Any]] = {}
    for index, item in enumerate([*products, *traffic], start=1):
        store_id = str(item.get("storeId") or "").strip()
        store_name = _clean_store_name(item, fallback=f"店铺 {index}")
        platform = _store_platform(item, fallback="导入平台")
        key = store_name or store_id or f"店铺 {index}"
        seen.setdefault(key, {"storeId": store_id, "storeName": store_name, "platform": platform})
    return list(seen.values())


def _active_task_count_for_store(store_id: str | None, active_tasks: List[Dict[str, Any]]) -> int:
    if not store_id:
        return 0
    return len([task for task in active_tasks if store_id in set(task.get("storeIds") or task.get("visibleStoreIds") or []) and task.get("displayState") != "backend_only"])


def build_store_rows(products: List[Dict[str, Any]], traffic: List[Dict[str, Any]], active_tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    products_by_store: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    traffic_by_store: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in products:
        key = _clean_store_name(item, fallback=str(item.get("storeId") or "未命名店铺"))
        products_by_store[key].append(item)
    for item in traffic:
        key = _clean_store_name(item, fallback=str(item.get("storeId") or "未命名店铺"))
        traffic_by_store[key].append(item)
    rows: List[Dict[str, Any]] = []
    for store in _visible_store_rows(products, traffic):
        store_name = str(store.get("storeName") or "店铺")
        store_id = str(store.get("storeId") or "")
        store_products = products_by_store.get(store_name, [])
        store_traffic = traffic_by_store.get(store_name, [])
        role_counter = Counter(_product_role(item) for item in store_products)
        product_role_tags = [f"{name} {count}" for name, count in role_counter.most_common()] or ["暂无商品"]
        tags = _business_tags(store_products)
        task_count = _active_task_count_for_store(store_id, active_tasks)
        store_weight = _store_weight_tag(store_products, store_traffic)
        rows.append({
            "storeId": store_id,
            "storeName": store_name,
            "displayName": store_name,
            "platform": store.get("platform"),
            "storeWeightTag": store_weight,
            "productCount": len(store_products),
            "trafficCount": len(store_traffic),
            "productRoleTags": product_role_tags[:4],
            "businessTags": tags[:4],
            "riskTags": tags[:4],
            "activeTaskCount": task_count,
            "alertCount": task_count,
            "taskIntensity": "有执行任务" if task_count else "标签观察",
            "level": _tag_level("执行任务" if task_count else " ".join(tags)),
            "judgment": f"{store_weight} · 商品 {len(store_products)} · 执行任务 {task_count}",
        })
    return rows


def _merge_store_rows(generated: List[Dict[str, Any]], master: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: Dict[str, Dict[str, Any]] = {}
    for row in [*master, *generated]:
        key = str(row.get("storeId") or row.get("storeName") or row.get("displayName") or "").strip()
        if not key:
            continue
        if key not in seen:
            seen[key] = dict(row)
        else:
            existing = seen[key]
            existing.update({k: v for k, v in row.items() if v not in {None, "", [], "—"}})
            existing["productCount"] = max(_as_int(existing.get("productCount")), _as_int(row.get("productCount")))
    return list(seen.values())


def build_operating_judgment(store_rows: List[Dict[str, Any]], task_counters: Dict[str, Any], *, object_missing: bool = False) -> Dict[str, Any]:
    active_tasks = _as_int(task_counters.get("visibleActive"), 0)
    tagged_stores = len([row for row in store_rows if row.get("businessTags") and row.get("businessTags") != ["常规观察"]])
    if object_missing:
        return {"title": "经营判断", "summary": "检测到报表数据或数据版本，但当前账号可读商品 / 店铺仍为 0。请在系统页执行经营对象回填，或重新导入报表。", "priority": "先修复经营对象入库，再生成任务", "mainRisk": "经营对象未入库", "taggedStoreCount": 0, "activeTaskCount": active_tasks, "objectSyncFailed": True}
    if active_tasks:
        summary = f"当前有 {active_tasks} 个执行任务，需要先处理高风险高时效事项。低风险信号已沉淀为店铺和商品标签。"
        main = "执行任务"
    else:
        summary = f"当前无需要立即处理的执行任务，{len(store_rows)} 个店铺、{sum(_as_int(row.get('productCount')) for row in store_rows)} 个商品已完成清洗入库。"
        main = "经营对象已更新"
    return {"title": "经营判断", "summary": summary, "priority": "先看经营对象，再处理执行任务", "mainRisk": main, "taggedStoreCount": tagged_stores, "activeTaskCount": active_tasks}


@router.get("/operating-unit")
def operating_unit(request: Request) -> Dict[str, Any]:
    user_id = user_id_from_headers(request.headers)
    user = current_user(user_id)
    projection = projection_summary(user_id)
    object_summary = operating_object_summary(user_id)
    v3 = get_v3_dashboard_summary(user_id)
    master_products = list_operating_products(user_id)
    master_stores = list_operating_stores(user_id)
    products = _merge_products(projected_products(user_id), master_products)
    traffic = projected_traffic(user_id)
    task_counters = get_task_counters_for_user(user_id)
    active_tasks = list_tasks(viewer_id=user_id, active_only=True)
    execution_tasks = [task for task in active_tasks if task.get("displayState") != "backend_only" and task.get("queueType") not in {"backend_tag", "store_product_tag", "observe_candidate"}]
    has_source_data = bool(projection.get("hasData") or v3.get("latestDataVersion") or traffic or execution_tasks)
    has_objects = bool(master_products or master_stores or object_summary.get("productCount") or object_summary.get("storeCount"))
    has_data = bool(has_objects or has_source_data)
    object_missing = bool(has_source_data and not has_objects and not products)
    if not has_data:
        return {
            "version": OPERATING_UNIT_VERSION,
            "hasData": False,
            "emptyState": "暂无数据",
            "syncState": {"label": "等待数据", "status": "empty"},
            "viewer": {"id": user.get("id"), "roleId": user.get("roleId"), "roleName": user.get("roleName")},
            "metrics": [],
            "storeRows": [],
            "operatingJudgment": None,
            "tasks": task_counters,
            "objectStore": object_summary,
        }
    if object_missing:
        return {
            "version": OPERATING_UNIT_VERSION,
            "hasData": True,
            "unitName": "经营单元",
            "syncState": {"label": "经营对象未入库", "status": "object_sync_failed", "latestDataVersion": projection.get("latestDataVersion") or v3.get("latestDataVersion")},
            "latestSnapshotAt": projection.get("latestSnapshotAt") or v3.get("latestSnapshotAt"),
            "viewer": {"id": user.get("id"), "roleId": user.get("roleId"), "roleName": user.get("roleName")},
            "metrics": [
                {"label": "店铺", "value": 0},
                {"label": "商品", "value": 0},
                {"label": "标签店铺", "value": 0},
                {"label": "执行任务", "value": len(execution_tasks)},
            ],
            "storeRows": [],
            "operatingJudgment": build_operating_judgment([], task_counters, object_missing=True),
            "tasks": task_counters,
            "objectStore": object_summary,
            "objectSyncFailed": True,
            "rule": "V11.10 fail closed：有数据版本但经营对象为 0 时，不允许显示经营对象已更新。",
        }
    store_rows = _merge_store_rows(build_store_rows(products, traffic, execution_tasks), master_stores)
    tagged_store_count = len([row for row in store_rows if row.get("businessTags") and row.get("businessTags") != ["常规观察"]])
    return {
        "version": OPERATING_UNIT_VERSION,
        "hasData": True,
        "unitName": "经营单元",
        "syncState": {"label": "数据已同步", "status": "synced", "latestDataVersion": object_summary.get("latestDataVersion") or projection.get("latestDataVersion") or v3.get("latestDataVersion")},
        "latestSnapshotAt": projection.get("latestSnapshotAt") or v3.get("latestSnapshotAt"),
        "viewer": {"id": user.get("id"), "roleId": user.get("roleId"), "roleName": user.get("roleName")},
        "metrics": [
            {"label": "店铺", "value": len(store_rows)},
            {"label": "商品", "value": len(products)},
            {"label": "标签店铺", "value": tagged_store_count},
            {"label": "执行任务", "value": len(execution_tasks)},
        ],
        "storeRows": store_rows,
        "operatingJudgment": build_operating_judgment(store_rows, task_counters),
        "tasks": task_counters,
        "objectStore": object_summary,
        "objectSyncFailed": False,
        "rule": "V11.10 经营单元只展示经营对象主档真实可读结果；导入成功必须绑定商品/店铺入库结果。",
    }
