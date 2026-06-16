"""Modular product API routes aligned to the frontend route registry."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from src.services.business_view_service import get_today_advice
from src.services.module_data_service import (
    COMPETITORS,
    LISTINGS,
    PRODUCTS,
    REPORT_DETAILS,
    REPORT_GROUPS,
    TRAFFIC,
    all_reports,
    clone,
    find_by_id,
)
from src.services.module_task_service import (
    complete_task,
    create_task,
    list_logs,
    list_tasks,
    pin_task,
    reorder_task,
    reset_tasks,
)

router = APIRouter(prefix="/api/modules", tags=["modules"])


def _find(collection: List[Dict[str, Any]], item_id: str, label: str) -> Dict[str, Any]:
    item = find_by_id(collection, item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"{label} not found")
    return item


@router.get("/dashboard")
def dashboard() -> Dict[str, Any]:
    payload = get_today_advice(write_outputs=True, record_logs=True)
    payload["tasks"] = list_tasks(active_only=True)[:5]
    payload["api_entry"] = "/api/modules/dashboard"
    return payload


@router.get("/operating-unit")
def operating_unit() -> Dict[str, Any]:
    return {
        "unitName": "家居生活店铺组",
        "platforms": ["淘宝", "拼多多", "抖音小店"],
        "storeCount": 4,
        "dataSources": ["ERP", "CRM"],
        "pendingSources": ["聚水潭", "广告后台"],
    }


@router.get("/product")
def product() -> List[Dict[str, Any]]:
    return clone(PRODUCTS)


@router.post("/product/{product_id}/tasks")
def product_task(product_id: str) -> Dict[str, Any]:
    item = _find(PRODUCTS, product_id, "product")
    risk_domain = "售后" if item["afterSalesLevel"] != "good" else "库存" if item["inventoryLevel"] == "danger" else "商品"
    high_risk = item["afterSalesLevel"] != "good" or item["inventoryLevel"] == "danger"
    return create_task({
        "entityType": "商品",
        "entityId": item["id"],
        "riskDomain": risk_domain,
        "actionType": "观察" if risk_domain == "商品" else "复查",
        "sourceModule": "商品经营列表",
        "source": "商品触发",
        "sourceRoute": "business-products",
        "productId": item["id"],
        "imageLabel": item["imageLabel"],
        "productShort": item["shortName"],
        "productTitle": item["title"],
        "title": item["title"],
        "platform": item["platform"],
        "store": item["store"],
        "link": item["link"],
        "priority": "高" if high_risk else "中",
        "priorityLevel": "danger" if high_risk else "warning",
        "deadline": "今天内" if high_risk else "明天前",
        "taskType": "售后复查" if item["afterSalesLevel"] != "good" else "库存承接" if item["inventoryLevel"] == "danger" else "商品优化",
        "taskSignal": "先查售后" if item["afterSalesLevel"] != "good" else "确认补货" if item["inventoryLevel"] == "danger" else "优化测试",
        "task": "复查售后原因，暂不扩大推广" if item["afterSalesLevel"] != "good" else "确认补货周期，再决定活动节奏" if item["inventoryLevel"] == "danger" else "加入商品优化观察",
        "reason": item["suggestion"],
        "judgmentTags": [item["inventoryStatus"], item["afterSales"], f"毛利 {item['grossMargin']}"],
    })


@router.get("/competitor")
def competitor() -> List[Dict[str, Any]]:
    return clone(COMPETITORS)


@router.post("/competitor/{competitor_id}/tasks")
def competitor_task(competitor_id: str) -> Dict[str, Any]:
    item = _find(COMPETITORS, competitor_id, "competitor")
    return create_task({
        "entityType": "竞品",
        "entityId": item["id"],
        "riskDomain": "风险" if item["status"] == "风险" else "上新",
        "actionType": "复查" if item["status"] == "风险" else "测试",
        "sourceModule": "竞品观察列表",
        "source": "竞品触发",
        "sourceRoute": "business-competitors",
        "productId": item["id"],
        "imageLabel": item["imageLabel"],
        "productShort": item["targetProduct"],
        "productTitle": item["title"],
        "title": item["title"],
        "platform": item["platform"],
        "store": item["store"],
        "priority": "高" if item["status"] == "风险" else "中",
        "priorityLevel": "danger" if item["status"] == "风险" else "warning",
        "deadline": "今天内" if item["status"] == "风险" else "明天前",
        "taskType": "竞品风险" if item["status"] == "风险" else "竞品机会",
        "taskSignal": item["opportunity"],
        "task": "复查竞品风险，不直接跟价" if item["status"] == "风险" else "生成对标测试任务",
        "reason": item["suggestion"],
        "judgmentTags": [item["pricePosition"], item["badReview"], item["status"]],
    })


@router.get("/listing")
def listing() -> List[Dict[str, Any]]:
    return clone(LISTINGS)


@router.post("/listing/{listing_id}/tasks")
def listing_task(listing_id: str) -> Dict[str, Any]:
    item = _find(LISTINGS, listing_id, "listing")
    return create_task({
        "entityType": "竞品机会" if item["mode"] == "competitor" else "商品",
        "entityId": item["id"],
        "riskDomain": "上新",
        "actionType": "复盘" if "复盘" in item["testType"] else "测试",
        "sourceModule": "上新测试台",
        "source": "上新触发",
        "sourceRoute": "business-listing",
        "productId": item["id"],
        "imageLabel": item["imageLabel"],
        "productShort": item["sourceName"],
        "productTitle": item["title"],
        "title": item["title"],
        "platform": item["platform"],
        "store": item["store"],
        "priority": "高" if item["statusLevel"] == "danger" else "中",
        "priorityLevel": item["statusLevel"],
        "deadline": item["due"],
        "taskType": item["testType"],
        "taskSignal": "确认测试版本",
        "task": f"{item['testType']}：{item['testPlan']}",
        "reason": f"{item['risk']} {item['suggestion']}",
        "judgmentTags": [item["sourceLabel"], item["testType"], item["targetMetric"]],
    })


@router.get("/traffic")
def traffic() -> List[Dict[str, Any]]:
    return clone(TRAFFIC)


@router.post("/traffic/{traffic_id}/tasks")
def traffic_task(traffic_id: str) -> Dict[str, Any]:
    item = _find(TRAFFIC, traffic_id, "traffic")
    text = f"{item['status']} {item['backflow']} {item['nextStep']}"
    risk_domain = "售后" if any(word in text for word in ["售后", "退款", "材质", "尺寸", "安装", "客服"]) else "库存" if any(word in text for word in ["库存", "补货", "承接"]) else "流量"
    return create_task({
        "entityType": "商品",
        "entityId": item["productId"],
        "riskDomain": risk_domain,
        "actionType": "观察" if risk_domain == "流量" and item["statusLevel"] == "good" else "复查",
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
    })


@router.get("/report")
def report() -> Dict[str, Any]:
    return {"reportGroups": clone(REPORT_GROUPS), "reportDetails": clone(REPORT_DETAILS)}


@router.get("/report/{report_id}")
def report_detail(report_id: str) -> Dict[str, Any]:
    if report_id not in REPORT_DETAILS:
        raise HTTPException(status_code=404, detail="report not found")
    return clone(REPORT_DETAILS[report_id])


@router.post("/report/{report_id}/tasks")
def report_task(report_id: str) -> Dict[str, Any]:
    item = _find(all_reports(), report_id, "report")
    return create_task({
        "entityType": "报表",
        "entityId": item["id"],
        "riskDomain": "报表",
        "actionType": "导入",
        "sourceModule": "ERP / CRM 报表管理",
        "source": "报表触发",
        "sourceRoute": "data-check",
        "productId": f"R-{item['id']}",
        "imageLabel": "表",
        "productShort": item["name"],
        "productTitle": f"{item['name']}导入后复盘",
        "title": f"{item['name']}导入后复盘",
        "platform": item["source"],
        "store": "家居生活店铺组",
        "productRoute": "data-check",
        "priority": "高" if item["id"] in {"refunds", "orders"} else "中",
        "priorityLevel": "danger" if item["id"] in {"refunds", "orders"} else "warning",
        "deadline": "今天内" if item["id"] in {"refunds", "orders"} else "本周内",
        "taskType": "报表复盘",
        "taskSignal": "导入后生成任务",
        "task": f"复盘{item['name']}，生成下一轮经营任务",
        "reason": f"{item['desc']}。导入后需要同步首页、待办和日志。",
        "judgmentTags": [item["source"], item["status"], item["count"]],
    })


@router.get("/todo")
def todo() -> Dict[str, Any]:
    return {"tasks": list_tasks(), "activeTasks": list_tasks(active_only=True)}


@router.post("/todo/{task_id}/complete")
def complete_todo(task_id: str) -> Dict[str, Any]:
    task = complete_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@router.post("/todo/{task_id}/pin")
def pin_todo(task_id: str) -> Dict[str, Any]:
    task = pin_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@router.post("/todo/{task_id}/reorder")
def reorder_todo(task_id: str, direction: str = "down") -> Dict[str, Any]:
    task = reorder_task(task_id, direction)
    if not task:
        raise HTTPException(status_code=400, detail="cannot reorder task")
    return task


@router.post("/todo/reset")
def reset_todo() -> Dict[str, Any]:
    return reset_tasks()


@router.get("/log")
def log() -> List[Dict[str, Any]]:
    return list_logs()
