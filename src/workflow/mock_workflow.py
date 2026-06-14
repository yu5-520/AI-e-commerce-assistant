"""Reusable Mock Workflow service.

This module is the single orchestration layer for both CLI and FastAPI.
It keeps the current implementation honest: API endpoints call the same
workflow that `python -m src.run_demo` uses.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

from src.category import build_category_context
from src.competitor import build_competitor_analysis
from src.data_loader.load_mock_data import load_all
from src.diagnosis.customer_segmentation import segment_customers
from src.diagnosis.product_diagnosis import diagnose_products
from src.listing import build_listing_growth_plan
from src.operating_loop import build_operating_loop_summary
from src.rag.simple_retriever import retrieve
from src.reports.generate_demo_report import write_json, write_markdown_report
from src.repositories.sqlite_repository import insert_report_record
from src.rpa_tasks.generate_task_draft import generate_customer_tasks, generate_product_tasks
from src.services.log_service import create_execution_log, create_workflow_run, finish_workflow_run
from src.traffic_test import build_traffic_feedback_report


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_mock_workflow_result(
    write_outputs: bool = False,
    record_logs: bool = False,
    category_id: str = "sun_protection_clothing",
) -> Dict[str, Any]:
    """Run the full mock workflow and return structured outputs.

    Args:
        write_outputs: When true, also write outputs/*.json and demo_report.md.
        record_logs: When true, write WorkflowRun and ExecutionLog records.
        category_id: Vertical category profile id injected into the workflow.

    Returns:
        A dictionary suitable for API responses and CLI report generation.
    """
    workflow_run_id = None
    if record_logs:
        run = create_workflow_run(
            workflow_type="full_mock_workflow",
            input_snapshot={"write_outputs": write_outputs, "category_id": category_id},
        )
        workflow_run_id = run["workflow_run_id"]

    try:
        category_context = build_category_context(category_id)
        if record_logs and workflow_run_id:
            create_execution_log(
                workflow_run_id=workflow_run_id,
                node_name="category_context",
                status="success",
                output_snapshot={
                    "category_id": category_context["category_profile"].get("category_id"),
                    "category_name": category_context["category_profile"].get("category_name"),
                    "source": category_context["category_profile"].get("source"),
                },
            )

        datasets = load_all()
        if record_logs and workflow_run_id:
            create_execution_log(
                workflow_run_id=workflow_run_id,
                node_name="load_mock_data",
                status="success",
                output_snapshot={key: len(value) for key, value in datasets.items()},
            )

        product_diagnosis = diagnose_products(
            products=datasets["products"],
            orders=datasets["orders"],
            inventory=datasets["inventory"],
            refunds=datasets["refunds"],
        )
        if record_logs and workflow_run_id:
            create_execution_log(
                workflow_run_id=workflow_run_id,
                node_name="product_diagnosis",
                status="success",
                output_snapshot={"product_count": len(product_diagnosis)},
            )

        customer_segmentation = segment_customers(
            customers=datasets["customers"],
            customer_tags=datasets["customer_tags"],
            interactions=datasets["interactions"],
        )
        if record_logs and workflow_run_id:
            create_execution_log(
                workflow_run_id=workflow_run_id,
                node_name="customer_segmentation",
                status="success",
                output_snapshot={"customer_count": len(customer_segmentation)},
            )

        competitor_analysis = build_competitor_analysis(product_diagnosis, category_context)
        if record_logs and workflow_run_id:
            create_execution_log(
                workflow_run_id=workflow_run_id,
                node_name="competitor_analysis",
                status="success",
                output_snapshot={
                    "analysis_id": competitor_analysis.get("analysis_id"),
                    "competitor_count": competitor_analysis.get("competitor_count"),
                    "reference_product": competitor_analysis.get("reference_product", {}).get("product_id"),
                },
            )

        listing_growth_plan = build_listing_growth_plan(category_context, competitor_analysis)
        if record_logs and workflow_run_id:
            create_execution_log(
                workflow_run_id=workflow_run_id,
                node_name="listing_growth_plan",
                status="success",
                output_snapshot={
                    "plan_id": listing_growth_plan.get("plan_id"),
                    "candidate_count": listing_growth_plan.get("candidate_count"),
                    "top_candidate": listing_growth_plan.get("top_candidate", {}).get("supplier_product_id"),
                },
            )

        traffic_feedback_report = build_traffic_feedback_report(category_context, listing_growth_plan)
        if record_logs and workflow_run_id:
            create_execution_log(
                workflow_run_id=workflow_run_id,
                node_name="traffic_feedback_report",
                status="success",
                output_snapshot={
                    "report_id": traffic_feedback_report.get("report_id"),
                    "experiment_count": traffic_feedback_report.get("experiment_count"),
                    "next_action": traffic_feedback_report.get("next_action"),
                },
            )

        operating_loop_summary = build_operating_loop_summary(
            category_context=category_context,
            product_diagnosis=product_diagnosis,
            customer_segmentation=customer_segmentation,
            competitor_analysis=competitor_analysis,
            listing_growth_plan=listing_growth_plan,
            traffic_feedback_report=traffic_feedback_report,
        )
        if record_logs and workflow_run_id:
            create_execution_log(
                workflow_run_id=workflow_run_id,
                node_name="operating_loop_summary",
                status="success",
                output_snapshot={
                    "loop_id": operating_loop_summary.get("loop_id"),
                    "loop_status": operating_loop_summary.get("loop_status"),
                    "next_module": operating_loop_summary.get("next_module"),
                },
            )

        category_name = category_context["category_profile"].get("category_name", "垂直类目")
        rag_context = {
            "category_profile": retrieve(f"{category_name} 价格带 季节性 尺码 退换 主图 SKU", top_k=3),
            "competitor_analysis": retrieve(f"{category_name} 竞品 价格带 差评 SKU 主图", top_k=3),
            "listing_growth": retrieve(f"{category_name} 上新 货盘 标题 主图 SKU 定价", top_k=3),
            "traffic_feedback": retrieve(f"{category_name} 流量 测试 点击 转化 退款 ROI 回流", top_k=3),
            "activity_price": retrieve("活动价 保本线 利润 风险", top_k=3),
            "after_sales": retrieve("退款 售后 客服 SOP 敏感客户", top_k=3),
            "customer_touch": retrieve("客户触达 隐私 自动群发 合规", top_k=3),
        }
        if record_logs and workflow_run_id:
            create_execution_log(
                workflow_run_id=workflow_run_id,
                node_name="rag_retrieval",
                status="success",
                output_snapshot={key: len(value) for key, value in rag_context.items()},
            )

        rpa_tasks = generate_product_tasks(product_diagnosis) + generate_customer_tasks(customer_segmentation)
        approval_required_tasks = [
            task for task in rpa_tasks if task.get("requires_approval") is True
        ]
        if record_logs and workflow_run_id:
            create_execution_log(
                workflow_run_id=workflow_run_id,
                node_name="task_generation",
                status="success",
                output_snapshot={
                    "rpa_task_count": len(rpa_tasks),
                    "approval_required_count": len(approval_required_tasks),
                },
            )

        result: Dict[str, Any] = {
            "workflow_name": "AI Vertical Shelf E-commerce Operating Loop Mock Workflow",
            "workflow_mode": "Workflow-first",
            "workflow_run_id": workflow_run_id,
            "category_context": category_context,
            "product_diagnosis": product_diagnosis,
            "customer_segmentation": customer_segmentation,
            "competitor_analysis": competitor_analysis,
            "listing_growth_plan": listing_growth_plan,
            "traffic_feedback_report": traffic_feedback_report,
            "operating_loop_summary": operating_loop_summary,
            "rpa_tasks": rpa_tasks,
            "approval_required_tasks": approval_required_tasks,
            "rag_context": rag_context,
            "summary": {
                "category_id": category_context["category_profile"].get("category_id"),
                "category_name": category_context["category_profile"].get("category_name"),
                "product_count": len(product_diagnosis),
                "customer_count": len(customer_segmentation),
                "competitor_count": competitor_analysis.get("competitor_count", 0),
                "listing_candidate_count": listing_growth_plan.get("candidate_count", 0),
                "top_listing_candidate": listing_growth_plan.get("top_candidate", {}).get("supplier_product_id"),
                "traffic_experiment_count": traffic_feedback_report.get("experiment_count", 0),
                "traffic_next_action": traffic_feedback_report.get("next_action"),
                "loop_status": operating_loop_summary.get("loop_status"),
                "loop_next_module": operating_loop_summary.get("next_module"),
                "rpa_task_count": len(rpa_tasks),
                "approval_required_count": len(approval_required_tasks),
                "auto_execution_allowed_count": sum(
                    1 for task in rpa_tasks if task.get("auto_execution_allowed") is True
                ),
            },
            "safety_boundary": {
                "auto_loop_execution": False,
                "auto_ad_account_operation": False,
                "auto_supplier_api": False,
                "auto_competitor_crawling": False,
                "auto_product_publish": False,
                "auto_price_change": False,
                "auto_campaign_registration": False,
                "auto_ad_spend_change": False,
                "auto_customer_message_blast": False,
                "auto_refund": False,
            },
        }

        if write_outputs:
            write_json("category_context.json", category_context)
            write_json("product_diagnosis.json", product_diagnosis)
            write_json("customer_segmentation.json", customer_segmentation)
            write_json("competitor_analysis.json", competitor_analysis)
            write_json("listing_growth_plan.json", listing_growth_plan)
            write_json("traffic_feedback_report.json", traffic_feedback_report)
            write_json("operating_loop_summary.json", operating_loop_summary)
            write_json("rpa_task_draft.json", rpa_tasks)
            write_json("approval_required_tasks.json", approval_required_tasks)
            write_json("rag_retrieval_context.json", rag_context)
            report_path = write_markdown_report(
                product_diagnosis,
                customer_segmentation,
                rpa_tasks,
                rag_context,
                category_context,
                competitor_analysis,
                listing_growth_plan,
                traffic_feedback_report,
                operating_loop_summary,
            )
            result["report_path"] = str(report_path)
            report_record = {
                "report_id": f"REPORT_{uuid4().hex[:10]}",
                "workflow_run_id": workflow_run_id,
                "report_type": "mock_workflow_report",
                "path": str(report_path),
                "format": "markdown",
                "created_at": now_iso(),
            }
            insert_report_record(report_record)
            result["report_record"] = report_record
            if record_logs and workflow_run_id:
                create_execution_log(
                    workflow_run_id=workflow_run_id,
                    node_name="report_output",
                    status="success",
                    output_snapshot={"report_path": str(report_path), "report_id": report_record["report_id"]},
                )

        if record_logs and workflow_run_id:
            finish_workflow_run(
                workflow_run_id=workflow_run_id,
                workflow_type="full_mock_workflow",
                status="success",
                output_snapshot=result["summary"],
            )

        return result
    except Exception as exc:
        if record_logs and workflow_run_id:
            create_execution_log(
                workflow_run_id=workflow_run_id,
                node_name="workflow_error",
                status="failed",
                error_message=str(exc),
            )
            finish_workflow_run(
                workflow_run_id=workflow_run_id,
                workflow_type="full_mock_workflow",
                status="failed",
                error_message=str(exc),
            )
        raise
