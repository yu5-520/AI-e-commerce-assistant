"""Reusable Mock Workflow service.

This module is the single orchestration layer for both CLI and FastAPI.
It keeps the current V7 implementation honest: API endpoints call the same
workflow that `python -m src.run_demo` uses.
"""

from __future__ import annotations

from typing import Any, Dict

from src.data_loader.load_mock_data import load_all
from src.diagnosis.customer_segmentation import segment_customers
from src.diagnosis.product_diagnosis import diagnose_products
from src.rag.simple_retriever import retrieve
from src.reports.generate_demo_report import write_json, write_markdown_report
from src.rpa_tasks.generate_task_draft import generate_customer_tasks, generate_product_tasks


def build_mock_workflow_result(write_outputs: bool = False) -> Dict[str, Any]:
    """Run the full mock workflow and return structured outputs.

    Args:
        write_outputs: When true, also write outputs/*.json and demo_report.md.

    Returns:
        A dictionary suitable for API responses and CLI report generation.
    """
    datasets = load_all()

    product_diagnosis = diagnose_products(
        products=datasets["products"],
        orders=datasets["orders"],
        inventory=datasets["inventory"],
        refunds=datasets["refunds"],
    )

    customer_segmentation = segment_customers(
        customers=datasets["customers"],
        customer_tags=datasets["customer_tags"],
        interactions=datasets["interactions"],
    )

    rag_context = {
        "activity_price": retrieve("活动价 保本线 利润 风险", top_k=3),
        "after_sales": retrieve("退款 售后 客服 SOP 敏感客户", top_k=3),
        "customer_touch": retrieve("客户触达 隐私 自动群发 合规", top_k=3),
    }

    rpa_tasks = generate_product_tasks(product_diagnosis) + generate_customer_tasks(customer_segmentation)
    approval_required_tasks = [
        task for task in rpa_tasks if task.get("requires_approval") is True
    ]

    result: Dict[str, Any] = {
        "workflow_name": "AI + RPA + ERP + CRM Mock Workflow",
        "workflow_mode": "Workflow-first",
        "product_diagnosis": product_diagnosis,
        "customer_segmentation": customer_segmentation,
        "rpa_tasks": rpa_tasks,
        "approval_required_tasks": approval_required_tasks,
        "rag_context": rag_context,
        "summary": {
            "product_count": len(product_diagnosis),
            "customer_count": len(customer_segmentation),
            "rpa_task_count": len(rpa_tasks),
            "approval_required_count": len(approval_required_tasks),
            "auto_execution_allowed_count": sum(
                1 for task in rpa_tasks if task.get("auto_execution_allowed") is True
            ),
        },
        "safety_boundary": {
            "auto_price_change": False,
            "auto_campaign_registration": False,
            "auto_ad_spend_change": False,
            "auto_customer_message_blast": False,
            "auto_refund": False,
        },
    }

    if write_outputs:
        write_json("product_diagnosis.json", product_diagnosis)
        write_json("customer_segmentation.json", customer_segmentation)
        write_json("rpa_task_draft.json", rpa_tasks)
        write_json("approval_required_tasks.json", approval_required_tasks)
        write_json("rag_retrieval_context.json", rag_context)
        report_path = write_markdown_report(
            product_diagnosis, customer_segmentation, rpa_tasks, rag_context
        )
        result["report_path"] = str(report_path)

    return result
