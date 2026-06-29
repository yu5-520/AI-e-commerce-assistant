"""Traffic module routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Request

from src.api.routes.modules.common import find_or_404
from src.services.account_service import user_id_from_headers
from src.services.module_projection_service import projected_traffic
from src.services.module_task_service import create_task, visible_candidates
from src.services.report_alert_service import attach_alert_state
from src.services.v1211_manual_task_package_service import wrap_manual_task_payload

router = APIRouter()


def traffic_task_payload(item: Dict[str, Any]) -> Dict[str, Any]:
    text = f"{item.get('status', '')} {item.get('backflow', '')} {item.get('nextStep', '')}"
    risk_domain = "售后" if any(word in text for word in ["售后", "退款", "材质", "尺寸", "安装", "客服"]) else "库存" if any(word in text for word in ["库存", "补货", "承接"]) else "流量"
    store_id = item.get("storeId")
    return {
        "entityType": "商品",
        "entityId": item["productId"],
        "riskDomain": risk_domain,
        "actionType": "观察" if risk_domain == "流量" and item.get("statusLevel") == "good" else "复查",
        "sourceType": "流量模块",
        "taskLayer": "operator_execution",
        "visibleRoleIds": ["manager", "operator", "finance"],
        "sourceModule": "流量模块",
        "source": "导入数据触发",
        "sourceRoute": "business-traffic",
        "productId": item["productId"],
        "storeIds": [store_id] if store_id else [],
        "visibleStoreIds": [store_id] if store_id else [],
        "imageLabel": item.get("imageLabel") or "流",
        "productShort": (item.get("title") or item["productId"])[:8],
        "productTitle": item.get("title") or item["productId"],
        "title": item.get("title") or item["productId"],
        "platform": item.get("platform") or "导入数据",
        "store": item.get("store") or "未绑定店铺",
        "link": item.get("link") or "",
        "priority": "高" if item.get("statusLevel") == "danger" else "中" if item.get("statusLevel") == "warning" else "低",
        "priorityLevel": item.get("statusLevel") or "warning",
        "deadline": "今天 18:00 前" if item.get("statusLevel") == "danger" else "明天前",
        "taskType": item.get("backflow") or "流量承接复查",
        "taskSignal": item.get("status") or "数据触发",
        "task": item.get("nextStep") or "根据导入数据复核流量承接。",
        "reason": f"{item.get('channel', '导入数据')} {item.get('source', '')}：成交 {item.get('roi', '—')}，库存 {item.get('inventory', '—')}。",
        "judgmentTags": [f"成交 {item.get('roi', '—')}", f"库存 {item.get('inventory', '—')}", item.get("status", "数据触发")],
    }


def with_alert_state(item: Dict[str, Any], user_id: str | None = None) -> Dict[str, Any]:
    return attach_alert_state(item, "商品", item["productId"], user_id=user_id)


@router.get("/traffic")
def traffic(request: Request) -> list[Dict[str, Any]]:
    user_id = user_id_from_headers(request.headers)
    items = projected_traffic(user_id)
    return [with_alert_state(item, user_id) for item in visible_candidates(items, traffic_task_payload)]


@router.post("/traffic/{traffic_id}/tasks")
def traffic_task(request: Request, traffic_id: str) -> Dict[str, Any]:
    user_id = user_id_from_headers(request.headers)
    item = find_or_404(projected_traffic(user_id), traffic_id, "traffic")
    return create_task(wrap_manual_task_payload(traffic_task_payload(item)))
