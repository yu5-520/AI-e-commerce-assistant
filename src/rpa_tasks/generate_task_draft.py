"""Generate low-risk RPA task drafts from diagnosis outputs."""

from __future__ import annotations

from typing import Dict, List

from src.approval.risk_rules import classify_task


def _build_task(
    task_id: str,
    task_type: str,
    ai_suggestion: str,
    target_product_id: str | None = None,
    target_customer_segment: str | None = None,
) -> Dict[str, object]:
    policy = classify_task(task_type)
    return {
        "task_id": task_id,
        "task_type": task_type,
        "target_product_id": target_product_id,
        "target_customer_segment": target_customer_segment,
        "risk_level": policy["risk_level"],
        "requires_approval": policy["requires_approval"],
        "auto_execution_allowed": policy["auto_execution_allowed"],
        "approval_status": "pending",
        "status": "pending_approval",
        "ai_suggestion": ai_suggestion,
        "policy_reason": policy["policy_reason"],
        "execution_result": {},
    }


def generate_product_tasks(product_diagnosis: List[Dict[str, object]]) -> List[Dict[str, object]]:
    tasks: List[Dict[str, object]] = []
    for index, item in enumerate(product_diagnosis, start=1):
        product_id = str(item["product_id"])
        risks = set(item.get("risks", []))

        tasks.append(
            _build_task(
                task_id=f"TASK_PRODUCT_DAILY_{index:03d}",
                task_type="daily_report",
                target_product_id=product_id,
                ai_suggestion=f"为商品 {product_id} 生成经营日报和下一轮复盘摘要。",
            )
        )

        if "activity_price_margin_risk" in risks or "high_inventory_low_order_risk" in risks:
            tasks.append(
                _build_task(
                    task_id=f"TASK_SKU_PRICE_{index:03d}",
                    task_type="sku_price_table",
                    target_product_id=product_id,
                    ai_suggestion="生成 SKU 价格建议表，标记保本线、活动价风险和人工确认项。",
                )
            )

        if "refund_abnormal_risk" in risks or "sensitive_category_compliance_risk" in risks:
            tasks.append(
                _build_task(
                    task_id=f"TASK_AFTER_SALES_{index:03d}",
                    task_type="after_sales_analysis",
                    target_product_id=product_id,
                    ai_suggestion="生成售后归因表，检查退款原因、详情页表达和客服话术。",
                )
            )

    return tasks


def generate_customer_tasks(customer_segments: List[Dict[str, object]]) -> List[Dict[str, object]]:
    tasks: List[Dict[str, object]] = []
    for index, item in enumerate(customer_segments, start=1):
        segment = str(item["segment"])
        customer_id = str(item["customer_id"])

        tasks.append(
            _build_task(
                task_id=f"TASK_CRM_SEGMENT_{index:03d}",
                task_type="customer_segmentation_report",
                target_customer_segment=segment,
                ai_suggestion=f"将客户 {customer_id} 纳入 {segment} 分层报告，并输出人工确认的运营建议。",
            )
        )

        if segment in {"高价值客户", "沉睡客户"}:
            tasks.append(
                _build_task(
                    task_id=f"TASK_RETENTION_{index:03d}",
                    task_type="retention_task_list",
                    target_customer_segment=segment,
                    ai_suggestion=f"生成 {segment} 的复购或召回任务草案，不自动触达客户。",
                )
            )

        if segment == "售后敏感客户":
            tasks.append(
                _build_task(
                    task_id=f"TASK_CRM_AFTER_SALES_{index:03d}",
                    task_type="after_sales_analysis",
                    target_customer_segment=segment,
                    ai_suggestion="售后敏感客户优先生成售后归因表，不直接营销触达。",
                )
            )

    return tasks
