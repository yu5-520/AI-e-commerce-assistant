"""Modular product API routes aligned to the frontend route registry.

Each endpoint maps to one frontend module under `web_demo/modules/*/page.js`.
The old `/api/business/*` compatibility layer has been removed from the active
entry so future updates can change one product module without disturbing others.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from src.services.approval_service import get_task_status_overrides, list_approval_records, update_task_status
from src.services.business_view_service import get_action_confirmations, get_today_advice

router = APIRouter(prefix="/api/modules", tags=["modules"])

PRODUCTS: List[Dict[str, Any]] = [
    {"id": "P001", "shortName": "遮阳伞", "title": "遮阳伞户外便携防晒防紫外线晴雨两用", "platform": "淘宝", "store": "家居生活主店", "imageLabel": "伞", "link": "https://shop.example.com/products/P001", "inventory": 200, "inventoryStatus": "库存偏高", "inventoryLevel": "warning", "price": 39, "cost": 18, "grossMargin": "53%", "afterSales": "正常", "afterSalesLevel": "good", "suggestion": "库存偏高但订单少，先做自然流量测试或清货活动测算。"},
    {"id": "P002", "shortName": "厨房置物架", "title": "厨房置物架免打孔收纳架壁挂多层家用置物架", "platform": "拼多多", "store": "家居百货店", "imageLabel": "架", "link": "https://shop.example.com/products/P002", "inventory": 120, "inventoryStatus": "正常", "inventoryLevel": "good", "price": 49, "cost": 22, "grossMargin": "55%", "afterSales": "退款偏高", "afterSalesLevel": "warning", "suggestion": "补充尺寸参照图和安装说明，降低安装预期偏差。"},
    {"id": "P003", "shortName": "护腰坐垫", "title": "护腰坐垫久坐办公室靠垫人体工学支撑款", "platform": "抖音小店", "store": "家居好物号", "imageLabel": "垫", "link": "https://shop.example.com/products/P003", "inventory": 80, "inventoryStatus": "待补货", "inventoryLevel": "danger", "price": 69, "cost": 35, "grossMargin": "49%", "afterSales": "售后敏感", "afterSalesLevel": "warning", "suggestion": "复查材质、支撑感描述和客服承诺，售后归因完成前不建议放量。"},
    {"id": "P004", "shortName": "收纳盒", "title": "透明收纳盒衣柜整理箱家用大容量防尘款", "platform": "淘宝", "store": "家居生活主店", "imageLabel": "盒", "link": "https://shop.example.com/products/P004", "inventory": 46, "inventoryStatus": "库存告急", "inventoryLevel": "danger", "price": 29, "cost": 13, "grossMargin": "55%", "afterSales": "正常", "afterSalesLevel": "good", "suggestion": "库存低于安全线，先确认补货周期和主推节奏。"},
]

COMPETITORS: List[Dict[str, Any]] = [
    {"id": "C001", "targetProduct": "厨房置物架", "title": "竞品：免打孔厨房置物架 304不锈钢款", "platform": "拼多多", "store": "竞品店 A", "imageLabel": "竞", "pricePosition": "低价压制", "badReview": "安装困难", "status": "机会", "opportunity": "补安装说明图", "suggestion": "把安装步骤、尺寸参照图转成上新测试版本。"},
    {"id": "C002", "targetProduct": "护腰坐垫", "title": "竞品：人体工学护腰坐垫升级款", "platform": "抖音小店", "store": "竞品店 B", "imageLabel": "竞", "pricePosition": "高价稳定", "badReview": "材质偏软", "status": "风险", "opportunity": "复查材质承诺", "suggestion": "不直接跟价，先复查本品材质、支撑感和客服承诺。"},
    {"id": "C003", "targetProduct": "遮阳伞", "title": "竞品：黑胶防晒晴雨伞便携款", "platform": "淘宝", "store": "竞品店 C", "imageLabel": "竞", "pricePosition": "同价竞争", "badReview": "收纳麻烦", "status": "机会", "opportunity": "强化便携卖点", "suggestion": "测试便携收纳主图，不直接降价。"},
]

LISTINGS: List[Dict[str, Any]] = [
    {"id": "L001", "sourceName": "遮阳伞", "title": "遮阳伞活动价测试", "platform": "淘宝", "store": "家居生活主店", "imageLabel": "伞", "mode": "product", "testType": "活动价确认", "testPlan": "平台券 + 利润安全线", "targetMetric": "ROI / 退款率", "statusLevel": "danger", "due": "今天 20:00 前", "risk": "活动价需要人工确认。", "suggestion": "确认利润安全线后再进入活动测试。", "sourceLabel": "商品"},
    {"id": "L002", "sourceName": "厨房置物架", "title": "厨房置物架详情页测试", "platform": "拼多多", "store": "家居百货店", "imageLabel": "架", "mode": "competitor", "testType": "详情页测试", "testPlan": "安装说明图 + 尺寸参照图", "targetMetric": "转化率 / 退款率", "statusLevel": "warning", "due": "明天 18:00 前", "risk": "竞品差评集中在安装与尺寸。", "suggestion": "先生成详情页测试版本。", "sourceLabel": "竞品机会"},
    {"id": "L003", "sourceName": "收纳盒", "title": "收纳盒 SKU 组合测试", "platform": "淘宝", "store": "家居生活主店", "imageLabel": "盒", "mode": "product", "testType": "SKU 复盘", "testPlan": "基础款 / 加厚款 / 组合款", "targetMetric": "转化率 / 库存占用", "statusLevel": "warning", "due": "3 天后复盘", "risk": "组合款占用库存。", "suggestion": "小范围测试后复盘。", "sourceLabel": "商品"},
]

TRAFFIC: List[Dict[str, Any]] = [
    {"id": "T001", "productId": "P002", "title": "厨房置物架免打孔收纳架壁挂多层家用置物架", "platform": "拼多多", "store": "家居百货店", "imageLabel": "架", "channel": "搜索推广", "source": "关键词测试", "exposure": "8,420", "ctr": "3.2%", "conversion": "1.1%", "roi": "1.1", "refundRate": "6.8%", "inventory": "120", "status": "先查售后", "statusLevel": "danger", "backflow": "售后复查", "nextStep": "先查安装和尺寸问题，不继续放大预算。", "link": "https://shop.example.com/products/P002"},
    {"id": "T002", "productId": "P003", "title": "护腰坐垫久坐办公室靠垫人体工学支撑款", "platform": "抖音小店", "store": "家居好物号", "imageLabel": "垫", "channel": "推荐流量", "source": "短视频测试", "exposure": "12,900", "ctr": "4.1%", "conversion": "0.8%", "roi": "0.9", "refundRate": "8.4%", "inventory": "80", "status": "暂停放量", "statusLevel": "danger", "backflow": "商品复查", "nextStep": "复查材质、支撑感和客服承诺。", "link": "https://shop.example.com/products/P003"},
    {"id": "T003", "productId": "P004", "title": "透明收纳盒衣柜整理箱家用大容量防尘款", "platform": "淘宝", "store": "家居生活主店", "imageLabel": "盒", "channel": "活动流量", "source": "平台券", "exposure": "5,600", "ctr": "2.8%", "conversion": "1.9%", "roi": "1.3", "refundRate": "2.1%", "inventory": "46", "status": "谨慎放量", "statusLevel": "warning", "backflow": "库存复查", "nextStep": "确认补货周期后再继续活动流量。", "link": "https://shop.example.com/products/P004"},
]

REPORT_GROUPS: List[Dict[str, Any]] = [
    {"title": "ERP 报表", "reports": [{"id": "products", "name": "商品报表", "source": "ERP", "status": "已同步", "count": "128 条", "desc": "商品、库存、成本、售价、毛利率"}, {"id": "orders", "name": "订单报表", "source": "ERP", "status": "已同步", "count": "932 条", "desc": "订单金额、发货状态、下单时间"}, {"id": "inventory", "name": "库存报表", "source": "ERP", "status": "已同步", "count": "128 条", "desc": "库存数量、预警、补货状态"}]},
    {"title": "CRM 报表", "reports": [{"id": "refunds", "name": "退款报表", "source": "CRM", "status": "已同步", "count": "37 条", "desc": "退款原因、售后状态、责任归因"}, {"id": "customers", "name": "客户报表", "source": "CRM", "status": "已同步", "count": "584 人", "desc": "客户来源、复购、风险标记"}]},
]

REPORT_DETAILS: Dict[str, Dict[str, Any]] = {
    "products": {"title": "商品报表", "source": "ERP", "summary": [["商品数", "128"], ["高风险商品", "3"], ["库存异常", "8"], ["售后敏感", "4"]], "columns": ["商品ID", "商品名称", "平台", "店铺", "库存", "售价", "状态"], "rows": [["P001", "遮阳伞", "淘宝", "家居生活主店", "200", "39", "正常"], ["P002", "厨房置物架", "拼多多", "家居百货店", "120", "49", "退款偏高"], ["P003", "护腰坐垫", "抖音小店", "家居好物号", "80", "69", "售后敏感"]]},
    "orders": {"title": "订单报表", "source": "ERP", "summary": [["今日订单", "86"], ["已发货", "61"], ["待发货", "18"], ["退款中", "7"]], "columns": ["订单号", "平台", "商品", "金额", "状态"], "rows": [["O001", "淘宝", "遮阳伞", "39", "已发货"], ["O002", "拼多多", "厨房置物架", "49", "待发货"], ["O003", "抖音小店", "护腰坐垫", "69", "退款中"]]},
    "inventory": {"title": "库存报表", "source": "ERP", "summary": [["SKU 数", "128"], ["库存偏高", "8"], ["库存偏低", "5"], ["待补货", "3"]], "columns": ["SKU", "商品", "库存", "安全库存", "状态"], "rows": [["SKU001", "遮阳伞", "200", "80", "库存偏高"], ["SKU002", "厨房置物架", "120", "60", "正常"], ["SKU003", "护腰坐垫", "80", "100", "待补货"]]},
    "refunds": {"title": "退款报表", "source": "CRM", "summary": [["退款记录", "37"], ["尺码问题", "9"], ["材质问题", "6"], ["物流问题", "4"]], "columns": ["退款ID", "平台", "商品", "金额", "原因", "状态"], "rows": [["R001", "抖音小店", "护腰坐垫", "69", "材质偏软", "处理中"], ["R002", "淘宝", "遮阳伞", "39", "物流延迟", "已完成"], ["R003", "拼多多", "厨房置物架", "49", "尺寸不符", "处理中"]]},
    "customers": {"title": "客户报表", "source": "CRM", "summary": [["客户数", "584"], ["复购客户", "96"], ["售后敏感", "23"], ["高价值", "41"]], "columns": ["客户ID", "来源平台", "最近购买", "消费金额", "标签", "状态"], "rows": [["C001", "淘宝", "遮阳伞", "156", "复购", "正常"], ["C002", "拼多多", "厨房置物架", "49", "价格敏感", "观察"], ["C003", "抖音小店", "护腰坐垫", "69", "售后敏感", "需跟进"]]},
}


def _find(collection: List[Dict[str, Any]], item_id: str, label: str) -> Dict[str, Any]:
    for item in collection:
        if item.get("id") == item_id:
            return item
    raise HTTPException(status_code=404, detail=f"{label} not found")


@router.get("/dashboard")
def dashboard() -> Dict[str, Any]:
    return get_today_advice(write_outputs=True, record_logs=True)


@router.get("/operating-unit")
def operating_unit() -> Dict[str, Any]:
    return {"unitName": "家居生活店铺组", "platforms": ["淘宝", "拼多多", "抖音小店"], "storeCount": 4, "dataSources": ["ERP", "CRM"], "pendingSources": ["聚水潭", "广告后台"]}


@router.get("/product")
def product() -> List[Dict[str, Any]]:
    return PRODUCTS


@router.post("/product/{product_id}/tasks")
def product_task(product_id: str) -> Dict[str, Any]:
    product_item = _find(PRODUCTS, product_id, "product")
    return {"sourceModule": "商品经营列表", "sourceRoute": "business-products", "productId": product_item["id"], "title": product_item["title"], "taskType": "商品复查", "reason": product_item["suggestion"]}


@router.get("/competitor")
def competitor() -> List[Dict[str, Any]]:
    return COMPETITORS


@router.post("/competitor/{competitor_id}/tasks")
def competitor_task(competitor_id: str) -> Dict[str, Any]:
    item = _find(COMPETITORS, competitor_id, "competitor")
    return {"sourceModule": "竞品观察列表", "sourceRoute": "business-competitors", "productId": item["id"], "title": item["title"], "taskType": "竞品观察", "reason": item["suggestion"]}


@router.get("/listing")
def listing() -> List[Dict[str, Any]]:
    return LISTINGS


@router.post("/listing/{listing_id}/tasks")
def listing_task(listing_id: str) -> Dict[str, Any]:
    item = _find(LISTINGS, listing_id, "listing")
    return {"sourceModule": "上新测试台", "sourceRoute": "business-listing", "productId": item["id"], "title": item["title"], "taskType": item["testType"], "reason": item["suggestion"]}


@router.get("/traffic")
def traffic() -> List[Dict[str, Any]]:
    return TRAFFIC


@router.post("/traffic/{traffic_id}/tasks")
def traffic_task(traffic_id: str) -> Dict[str, Any]:
    item = _find(TRAFFIC, traffic_id, "traffic")
    return {"sourceModule": "流量测试台", "sourceRoute": "business-traffic", "productId": item["productId"], "title": item["title"], "taskType": item["backflow"], "reason": item["nextStep"]}


@router.get("/report")
def report() -> Dict[str, Any]:
    return {"reportGroups": REPORT_GROUPS, "reportDetails": REPORT_DETAILS}


@router.get("/report/{report_id}")
def report_detail(report_id: str) -> Dict[str, Any]:
    if report_id not in REPORT_DETAILS:
        raise HTTPException(status_code=404, detail="report not found")
    return REPORT_DETAILS[report_id]


@router.post("/report/{report_id}/tasks")
def report_task(report_id: str) -> Dict[str, Any]:
    reports = [report for group in REPORT_GROUPS for report in group["reports"]]
    item = _find(reports, report_id, "report")
    return {"sourceModule": "ERP / CRM 报表管理", "sourceRoute": "data-check", "productId": f"R-{item['id']}", "title": f"{item['name']}导入后复盘", "taskType": "报表复盘", "reason": item["desc"]}


@router.get("/todo")
def todo() -> Dict[str, Any]:
    payload = get_action_confirmations()
    overrides = get_task_status_overrides()
    if overrides:
        payload["overrides"] = overrides
    return payload


@router.post("/todo/{task_id}/complete")
def complete_todo(task_id: str) -> Dict[str, Any]:
    return update_task_status(task_id=task_id, status="approved")


@router.get("/log")
def log() -> List[Dict[str, Any]]:
    return list_approval_records()
