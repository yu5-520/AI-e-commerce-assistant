"""Rule-based CRM customer segmentation for the mock workflow."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from src.data_loader.load_mock_data import to_int, to_number


def _group_by(rows: List[Dict[str, str]], key: str) -> Dict[str, List[Dict[str, str]]]:
    grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row.get(key, "")].append(row)
    return grouped


def segment_customers(
    customers: List[Dict[str, str]],
    customer_tags: List[Dict[str, str]],
    interactions: List[Dict[str, str]],
) -> List[Dict[str, object]]:
    tags_by_customer = _group_by(customer_tags, "customer_id")
    interactions_by_customer = _group_by(interactions, "customer_id")

    results: List[Dict[str, object]] = []

    for customer in customers:
        customer_id = customer["customer_id"]
        total_orders = to_int(customer.get("total_orders"))
        total_amount = to_number(customer.get("total_amount"))
        refund_count = to_int(customer.get("refund_count"))
        rfm_score = customer.get("rfm_score", "")
        existing_tags = [row.get("tag_name", "") for row in tags_by_customer.get(customer_id, [])]
        customer_interactions = interactions_by_customer.get(customer_id, [])
        negative_interaction_count = sum(
            1 for row in customer_interactions if row.get("sentiment") == "negative"
        )

        tags = set(tag for tag in existing_tags if tag)
        basis: List[str] = []
        recommended_actions: List[str] = []
        risk_notes: List[str] = []
        segment = customer.get("customer_level") or "普通客户"
        risk_level = "low"

        if total_orders >= 5 and total_amount >= 500 and refund_count == 0:
            segment = "高价值客户"
            tags.add("高价值")
            tags.add("复购潜力")
            basis.append("累计订单和消费金额较高，且退款次数低")
            recommended_actions.append("生成老客复购任务草案")

        if total_orders <= 1:
            segment = "新客"
            tags.add("新客")
            basis.append("购买次数较少，处于新客阶段")
            recommended_actions.append("生成新客关怀和使用说明话术草案")

        if "沉睡客户" in existing_tags or rfm_score.startswith("R1"):
            segment = "沉睡客户"
            tags.add("沉睡客户")
            basis.append("最近购买时间较远或 RFM 活跃度较低")
            recommended_actions.append("生成低频召回任务表，避免频繁打扰")
            risk_level = "medium"

        if refund_count >= 2 or negative_interaction_count > 0 or "售后敏感客户" in existing_tags:
            segment = "售后敏感客户"
            tags.add("售后敏感")
            tags.add("流失风险")
            basis.append("退款次数或负面互动较高")
            recommended_actions.append("优先生成售后归因表和客服 SOP 优化草案")
            risk_notes.append("不建议直接营销触达，需先处理售后原因")
            risk_level = "high"

        if not basis:
            basis.append("当前数据不足以判断强标签，保守归为普通客户")
            recommended_actions.append("继续观察订单和互动数据")

        results.append(
            {
                "customer_id": customer_id,
                "segment": segment,
                "rfm_score": rfm_score,
                "tags": sorted(tags),
                "basis": basis,
                "recommended_actions": recommended_actions,
                "risk_level": risk_level,
                "risk_notes": risk_notes,
                "requires_human_approval": True,
                "auto_execution_allowed": False,
            }
        )

    return results
