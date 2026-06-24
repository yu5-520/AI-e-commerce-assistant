"""V10.7 Agent operating profile service.

Tags are Agent working memory, not a required user operation. The user can edit
or override labels, but normal classification is automatic and becomes visible
only when a tag drift should create a task.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List

V107_OPERATING_PROFILE_VERSION = "10.7.0"
V107_PROFILE_RULES = [
    "agent_assigns_tags_without_user_confirmation",
    "tags_are_agent_working_language",
    "user_can_edit_but_does_not_confirm_by_default",
    "tag_drift_becomes_task_when_business_data_keeps_declining",
    "profile_is_used_before_agent_task_generation",
]
V107_TAG_TYPES = ["vertical_category", "store_weight", "product_role", "risk", "task_intensity"]


def _rows(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    values = result.get("rows") if isinstance(result.get("rows"), list) else []
    out = [item for item in values if isinstance(item, dict)]
    for child in result.get("results", []) if isinstance(result.get("results"), list) else []:
        if isinstance(child, dict):
            out.extend(_rows(child))
    return out


def _dataset_names(result: Dict[str, Any]) -> List[str]:
    values: List[str] = []
    if result.get("datasetName"):
        values.append(str(result["datasetName"]))
    for child in result.get("results", []) if isinstance(result.get("results"), list) else []:
        if isinstance(child, dict):
            values.extend(_dataset_names(child))
    return list(dict.fromkeys(values))


def _store_id(row: Dict[str, Any]) -> str:
    return str(row.get("store_id") or row.get("storeId") or row.get("shop_id") or row.get("shopId") or "S001")


def _product_id(row: Dict[str, Any]) -> str:
    return str(row.get("product_id") or row.get("productId") or row.get("sku_id") or row.get("skuId") or row.get("id") or "P001")


def _title(row: Dict[str, Any]) -> str:
    return str(row.get("title") or row.get("product_title") or row.get("productTitle") or row.get("name") or "商品")


def _number(row: Dict[str, Any], *keys: str) -> float:
    for key in keys:
        if key in row and row.get(key) not in {None, ""}:
            try:
                return float(row.get(key))
            except (TypeError, ValueError):
                continue
    return 0.0


def infer_vertical_tags(text: str) -> List[str]:
    value = text.lower()
    tags: List[str] = []
    if any(word in value for word in ["防晒", "sun", "uv"]):
        tags.extend(["夏季防晒", "功能型服饰"])
    if any(word in value for word in ["衣", "服", "裙", "裤", "coat", "shirt"]):
        tags.append("服饰")
    if any(word in value for word in ["鞋", "靴", "sneaker"]):
        tags.append("鞋靴")
    if any(word in value for word in ["包", "bag"]):
        tags.append("箱包")
    return list(dict.fromkeys(tags or ["待识别类目"]))


def infer_product_role(row: Dict[str, Any]) -> str:
    sales = _number(row, "sales", "sale_count", "salesCount", "orders")
    traffic = _number(row, "traffic", "views", "pv", "impressions")
    stock = _number(row, "stock", "inventory")
    roi = _number(row, "roi", "ROI")
    if sales >= 100 or traffic >= 1000 or roi >= 2.0:
        return "主推款"
    if stock >= 200 and sales < 20:
        return "清库存款"
    if traffic < 100 and sales < 10:
        return "测试款"
    return "常规款"


def infer_risk_tags(row: Dict[str, Any]) -> List[str]:
    tags: List[str] = []
    stock = _number(row, "stock", "inventory")
    sales = _number(row, "sales", "sale_count", "salesCount", "orders")
    conversion = _number(row, "conversion", "conversion_rate", "cvr")
    roi = _number(row, "roi", "ROI")
    refund = _number(row, "refund_rate", "refundRate", "refund")
    if stock >= 200 and sales < 20:
        tags.append("高库存低动销")
    if conversion and conversion < 0.02:
        tags.append("高曝光低转化")
    if roi and roi < 1.0:
        tags.append("ROI偏低")
    if refund and refund > 0.08:
        tags.append("退款风险")
    return tags or ["常规观察"]


def infer_store_weight(rows: Iterable[Dict[str, Any]]) -> str:
    rows = list(rows)
    total_sales = sum(_number(row, "sales", "sale_count", "salesCount", "orders") for row in rows)
    total_traffic = sum(_number(row, "traffic", "views", "pv", "impressions") for row in rows)
    avg_roi = sum(_number(row, "roi", "ROI") for row in rows) / max(1, len(rows))
    if total_sales >= 300 or total_traffic >= 5000 or avg_roi >= 2.0:
        return "高权重店铺"
    if total_sales <= 30 and total_traffic <= 500:
        return "测试店铺"
    return "常规店铺"


def build_agent_operating_profile(result: Dict[str, Any]) -> Dict[str, Any]:
    rows = _rows(result)
    stores: Dict[str, List[Dict[str, Any]]] = {}
    products: List[Dict[str, Any]] = []
    for row in rows:
        store_id = _store_id(row)
        stores.setdefault(store_id, []).append(row)
        title = _title(row)
        products.append(
            {
                "productId": _product_id(row),
                "storeId": store_id,
                "title": title,
                "verticalCategoryTags": infer_vertical_tags(title),
                "productRoleTag": infer_product_role(row),
                "riskTags": infer_risk_tags(row),
                "taskIntensityTag": "强处理" if "ROI偏低" in infer_risk_tags(row) and infer_product_role(row) == "主推款" else "常规处理",
            }
        )
    store_profiles = [
        {
            "storeId": store_id,
            "storeWeightTag": infer_store_weight(store_rows),
            "productCount": len(store_rows),
            "agentUse": "生成任务前先读取店铺权重和商品角色。",
        }
        for store_id, store_rows in stores.items()
    ]
    tag_change_task_candidates = [
        {
            "taskType": "tag_change_task",
            "entityType": "product",
            "entityId": item["productId"],
            "reason": "商品风险标签持续变化时，系统以任务形式提醒用户处理。",
            "tags": item["riskTags"],
        }
        for item in products
        if any(tag in item["riskTags"] for tag in ["高库存低动销", "ROI偏低", "退款风险"])
    ][:10]
    return {
        "version": V107_OPERATING_PROFILE_VERSION,
        "mode": "agent_operating_profile",
        "datasetNames": _dataset_names(result),
        "rules": V107_PROFILE_RULES,
        "tagTypes": V107_TAG_TYPES,
        "userConfirmationRequired": False,
        "userCanEditTags": True,
        "stores": store_profiles,
        "products": products[:50],
        "tagChangeTaskCandidates": tag_change_task_candidates,
        "agentContextRule": "Agent 生成任务前先读取经营档案，不让用户默认确认标签。",
    }


def attach_v107_operating_profile(result: Dict[str, Any]) -> Dict[str, Any]:
    payload = deepcopy(result)
    payload["v107OperatingProfile"] = build_agent_operating_profile(payload)
    payload["agentOperatingProfileVersion"] = V107_OPERATING_PROFILE_VERSION
    return payload
