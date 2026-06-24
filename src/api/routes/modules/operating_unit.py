"""Operating unit route for productized store tags and business judgment."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List

from fastapi import APIRouter, Request

from src.services.account_service import current_user, user_id_from_headers
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


def _risk_tags(products: List[Dict[str, Any]], active_alert_count: int) -> List[str]:
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


def build_operating_tags(products: List[Dict[str, Any]], traffic: List[Dict[str, Any]], v3: Dict[str, Any], task_counters: Dict[str, Any]) -> Dict[str, Any]:
    active_alert_count = _as_int(v3.get("activeAlertCount"), 0)
    active_tasks = _as_int(task_counters.get("visibleActive"), 0)
    store_weight = _store_weight_tag(products, traffic)
    role_counter = Counter(_product_role(item) for item in products)
    product_roles = [f"{name} {count}" for name, count in role_counter.most_common()] or ["暂无商品"]
    risk_tags = _risk_tags(products, active_alert_count)
    task_intensity = "强处理" if active_alert_count >= 2 or active_tasks >= 5 or any(tag != "常规观察" for tag in risk_tags) else "常规处理"
    main_risk = _main_risk(risk_tags)
    priority = "先处理风险商品，再复核流量承接。" if main_risk != "常规观察" else "保持观察，等待下一轮数据同步。"
    return {
        "cards": [
            {"label": "店铺权重", "value": store_weight, "level": _tag_level(store_weight), "tags": [f"店铺 {_store_count(products)}", f"商品 {len(products)}"]},
            {"label": "商品结构", "value": product_roles[0], "level": _tag_level(product_roles[0]), "tags": product_roles[:4]},
            {"label": "风险标签", "value": main_risk, "level": _tag_level(main_risk), "tags": risk_tags[:4]},
            {"label": "任务强度", "value": task_intensity, "level": _tag_level(task_intensity), "tags": [f"任务 {active_tasks}", f"预警 {active_alert_count}"]},
        ],
        "judgment": {
            "title": "经营判断",
            "summary": f"当前经营单元以{main_risk}为主要信号，任务强度为{task_intensity}。{priority}",
            "priority": priority,
            "mainRisk": main_risk,
        },
    }


@router.get("/operating-unit")
def operating_unit(request: Request) -> Dict[str, Any]:
    user_id = user_id_from_headers(request.headers)
    user = current_user(user_id)
    projection = projection_summary(user_id)
    v3 = get_v3_dashboard_summary(user_id)
    products = projected_products(user_id)
    traffic = projected_traffic(user_id)
    task_counters = get_task_counters_for_user(user_id)
    active_alert_count = _as_int(v3.get("activeAlertCount"), 0)
    active_tasks = _as_int(task_counters.get("visibleActive"), 0)
    has_data = bool(projection.get("hasData") or v3.get("latestDataVersion") or products or traffic or active_alert_count)
    if not has_data:
        return {
            "version": "5.1.0",
            "hasData": False,
            "emptyState": "暂无数据",
            "syncState": {"label": "等待数据", "status": "empty"},
            "viewer": {"id": user.get("id"), "roleId": user.get("roleId"), "roleName": user.get("roleName")},
            "metrics": [],
            "storeTags": [],
            "operatingJudgment": None,
            "tasks": task_counters,
        }
    tag_payload = build_operating_tags(products, traffic, v3, task_counters)
    return {
        "version": "5.1.0",
        "hasData": True,
        "unitName": "经营单元",
        "syncState": {"label": "数据已同步", "status": "synced", "latestDataVersion": projection.get("latestDataVersion") or v3.get("latestDataVersion")},
        "latestSnapshotAt": projection.get("latestSnapshotAt") or v3.get("latestSnapshotAt"),
        "viewer": {"id": user.get("id"), "roleId": user.get("roleId"), "roleName": user.get("roleName")},
        "metrics": [
            {"label": "店铺", "value": _store_count(products)},
            {"label": "商品", "value": len(products)},
            {"label": "风险", "value": active_alert_count},
            {"label": "任务", "value": active_tasks},
        ],
        "storeTags": tag_payload["cards"],
        "operatingJudgment": tag_payload["judgment"],
        "tasks": task_counters,
        "projection": projection,
        "v3": v3,
    }
