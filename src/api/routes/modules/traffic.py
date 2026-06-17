"""Traffic module routes."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

from src.api.routes.modules.common import find_or_404
from src.services.module_data_service import TRAFFIC
from src.services.module_task_service import create_task, visible_candidates
from src.services.report_alert_service import attach_alert_state

router = APIRouter()


def traffic_task_payload(item: Dict[str, Any]) -> Dict[str, Any]:
    text = f"{item['status']} {item['backflow']} {item['nextStep']}"
    risk_domain = "售后" if any(word in text for word in ["售后", "退款", "材质", "尺寸", "安装", "客服"]) else "库存" if any(word in text for word in ["库存", "补货", "承接"]) else "流量"
    return {
        "entityType": "商品",
        "entityId": item["productId"],
        "riskDomain": risk_domain,
        "actionType": "观察" if risk_domain == "流量" and item["statusLevel"] == "good" else "复查",
        "sourceType": "流量模块",
        "taskLayer": "operator_execution",
        "visibleRoleIds": ["manager", "operator", "finance"],
        "sourceModule": "流量测试台",
        "source": "流量触发",
        "sourceRoute": "business-traffic",
        "productId": item["productId"],
        "imageLabel": item["imageLabel"],
        "productShort": item["title"][:6],
        "productTitle": item["title"],
        "title": item["title"],
        "platform": item["platform"],
        "store": item["store"],
        "link": item["link"],
        "priority": "高" if item["statusLevel"] == "danger" else "中" if item["statusLevel"] == "warning" else "低",
        "priorityLevel": item["statusLevel"],
        "deadline": "今天 18:00 前" if item["statusLevel"] == "danger" else "明天前",
        "taskType": item["backflow"],
        "taskSignal": item["status"],
        "task": item["nextStep"],
        "reason": f"{item['channel']} {item['source']}：ROI {item['roi']}，退款率 {item['refundRate']}，库存 {item['inventory']}。",
        "judgmentTags": [f"ROI {item['roi']}", f"退款率 {item['refundRate']}", item["status"]],
    }


def with_alert_state(item: Dict[str, Any]) -> Dict[str, Any]:
    return attach_alert_state(item, "商品", item["productId"])


@router.get("/traffic")
def traffic() -> List[Dict[str, Any]]:
    return [with_alert_state(item) for item in visible_candidates(TRAFFIC, traffic_task_payload)]


@router.post("/traffic/{traffic_id}/tasks")
def traffic_task(traffic_id: str) -> Dict[str, Any]:
    item = find_or_404(TRAFFIC, traffic_id, "traffic")
    return create_task(traffic_task_payload(item))
