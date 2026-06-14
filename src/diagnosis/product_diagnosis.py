"""Rule-based product diagnosis for the mock ERP workflow.

The current MVP uses transparent rules to simulate the AI diagnosis node.
Later this module can be replaced by an LLM + RAG decision node while keeping
its structured output contract stable.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from src.data_loader.load_mock_data import to_int, to_number


def _group_by(rows: List[Dict[str, str]], key: str) -> Dict[str, List[Dict[str, str]]]:
    grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row.get(key, "")].append(row)
    return grouped


def diagnose_products(
    products: List[Dict[str, str]],
    orders: List[Dict[str, str]],
    inventory: List[Dict[str, str]],
    refunds: List[Dict[str, str]],
) -> List[Dict[str, object]]:
    orders_by_product = _group_by(orders, "product_id")
    inventory_by_product = _group_by(inventory, "product_id")
    refunds_by_product = _group_by(refunds, "product_id")

    results: List[Dict[str, object]] = []

    for product in products:
        product_id = product["product_id"]
        product_orders = orders_by_product.get(product_id, [])
        product_inventory = inventory_by_product.get(product_id, [])
        product_refunds = refunds_by_product.get(product_id, [])

        cost_price = to_number(product.get("cost_price"))
        sale_price = to_number(product.get("sale_price"))
        activity_price = to_number(product.get("activity_price"))
        shipping_cost = to_number(product.get("shipping_cost"))
        stock = to_int(product.get("stock"))

        order_count = sum(to_int(row.get("quantity"), 1) for row in product_orders)
        revenue = sum(to_number(row.get("actual_paid")) for row in product_orders)
        refund_count = len(product_refunds)
        refund_rate = refund_count / max(len(product_orders), 1)
        gross_margin = sale_price - cost_price - shipping_cost
        activity_margin = activity_price - cost_price - shipping_cost

        risks: List[str] = []
        suggested_actions: List[str] = []
        risk_level = "low"

        if gross_margin <= 0:
            risks.append("sale_price_below_cost_risk")
            suggested_actions.append("复核成本、物流与售价，暂停放量")
            risk_level = "high"

        if activity_margin <= 0:
            risks.append("activity_price_margin_risk")
            suggested_actions.append("活动价接近或低于保本线，报名活动前必须人工确认")
            risk_level = "high" if risk_level == "high" else "medium"

        if stock >= 150 and order_count <= 2:
            risks.append("high_inventory_low_order_risk")
            suggested_actions.append("库存偏高但订单少，建议先做自然流测试或清货活动测算")
            risk_level = "medium" if risk_level == "low" else risk_level

        if refund_rate >= 0.3:
            risks.append("refund_abnormal_risk")
            suggested_actions.append("退款率偏高，建议进入售后归因工作流")
            risk_level = "high" if refund_rate >= 0.5 else "medium"

        if product.get("is_sensitive_category", "false").lower() == "true":
            risks.append("sensitive_category_compliance_risk")
            suggested_actions.append("敏感类目，生成标题、主图和客服话术前必须先做合规检查")
            risk_level = "high" if risk_level == "high" else "medium"

        if not risks:
            suggested_actions.append("基础经营风险较低，可继续生成标题、主图、SKU 或日报任务")

        results.append(
            {
                "product_id": product_id,
                "product_name": product.get("product_name"),
                "order_count": order_count,
                "revenue": round(revenue, 2),
                "stock": stock,
                "refund_count": refund_count,
                "refund_rate": round(refund_rate, 4),
                "gross_margin": round(gross_margin, 2),
                "activity_margin": round(activity_margin, 2),
                "risk_level": risk_level,
                "risks": risks,
                "suggested_actions": suggested_actions,
            }
        )

    return results
