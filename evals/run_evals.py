"""Minimal eval runner for the mock workflow.

Usage:
    python evals/run_evals.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.category import build_category_context  # noqa: E402
from src.competitor import build_competitor_analysis  # noqa: E402
from src.data_loader.load_mock_data import load_all  # noqa: E402
from src.diagnosis.customer_segmentation import segment_customers  # noqa: E402
from src.diagnosis.product_diagnosis import diagnose_products  # noqa: E402
from src.listing import build_listing_growth_plan  # noqa: E402
from src.operating_loop import build_operating_loop_summary  # noqa: E402
from src.operating_unit import infer_operating_unit  # noqa: E402
from src.rag.simple_retriever import retrieve  # noqa: E402
from src.rpa_tasks.generate_task_draft import generate_customer_tasks  # noqa: E402
from src.scheduler import build_cycle_policy  # noqa: E402
from src.traffic_test import build_traffic_feedback_report  # noqa: E402


def _build_erp_inferred_context() -> tuple[dict, dict, dict, list[dict]]:
    datasets = load_all()
    operating_unit = infer_operating_unit(
        products=datasets["products"],
        orders=datasets["orders"],
        inventory=datasets["inventory"],
    )
    cycle_policy = build_cycle_policy(operating_unit)
    category_context = build_category_context(
        str(operating_unit["category_profile_id"]),
        operating_unit=operating_unit,
    )
    product_diagnosis = diagnose_products(
        products=datasets["products"],
        orders=datasets["orders"],
        inventory=datasets["inventory"],
        refunds=datasets["refunds"],
    )
    return operating_unit, cycle_policy, category_context, product_diagnosis


def run_crm_segmentation_eval() -> dict:
    datasets = load_all()
    segments = segment_customers(
        customers=datasets["customers"],
        customer_tags=datasets["customer_tags"],
        interactions=datasets["interactions"],
    )
    c004 = next(item for item in segments if item["customer_id"] == "C004")
    passed = (
        c004["segment"] == "售后敏感客户"
        and c004["requires_human_approval"] is True
        and c004["auto_execution_allowed"] is False
    )
    return {
        "eval_id": "crm_segmentation_eval_001",
        "passed": passed,
        "observed": c004,
    }


def run_rpa_task_eval() -> dict:
    datasets = load_all()
    segments = segment_customers(
        customers=datasets["customers"],
        customer_tags=datasets["customer_tags"],
        interactions=datasets["interactions"],
    )
    tasks = generate_customer_tasks(segments)
    forbidden_types = {
        "auto_price_change",
        "auto_campaign_registration",
        "auto_message_blast",
        "auto_refund",
    }
    passed = all(
        task["task_type"] not in forbidden_types
        and task["requires_approval"] is True
        and task["auto_execution_allowed"] is False
        for task in tasks
    )
    return {
        "eval_id": "rpa_task_eval_001",
        "passed": passed,
        "observed_task_count": len(tasks),
        "observed_task_types": sorted({task["task_type"] for task in tasks}),
    }


def run_operating_unit_eval() -> dict:
    operating_unit, cycle_policy, category_context, _product_diagnosis = _build_erp_inferred_context()
    passed = (
        operating_unit["base_source"] == "ERP product data"
        and operating_unit["category_profile_id"] == "home_living_goods"
        and category_context["category_profile"]["category_name"] == "家居生活商品"
        and cycle_policy["cycle_frequency"] == "daily"
    )
    return {
        "eval_id": "operating_unit_eval_001",
        "passed": passed,
        "observed_operating_unit": operating_unit,
        "observed_cycle_policy": cycle_policy,
    }


def run_category_profile_eval() -> dict:
    _operating_unit, _cycle_policy, context, _product_diagnosis = _build_erp_inferred_context()
    profile = context["category_profile"]
    hits = retrieve("家居生活商品 价格带 尺寸 收纳 流量 回流", top_k=3)
    passed = (
        profile["category_name"] == "家居生活商品"
        and bool(profile["price_bands"])
        and bool(profile["common_return_reasons"])
        and any(hit.get("source") == "category_profiles/home_living_goods.md" for hit in hits)
    )
    return {
        "eval_id": "category_profile_eval_001",
        "passed": passed,
        "observed_category": profile["category_name"],
        "observed_source": profile["source"],
        "rag_sources": [hit.get("source") for hit in hits],
    }


def run_competitor_analysis_eval() -> dict:
    _operating_unit, _cycle_policy, category_context, product_diagnosis = _build_erp_inferred_context()
    analysis = build_competitor_analysis(product_diagnosis, category_context)
    passed = (
        analysis["category_name"] == "家居生活商品"
        and analysis["data_source"] == "examples/category_home_living/mock_competitors.csv"
        and analysis["competitor_count"] > 0
        and bool(analysis["reference_product"]["trigger_reason"])
        and bool(analysis["price_gap"]["insight"])
        and bool(analysis["review_gap"]["opportunity_actions"])
        and analysis["safe_use_policy"].startswith("只拆解")
    )
    return {
        "eval_id": "competitor_analysis_eval_001",
        "passed": passed,
        "observed_reference_product": analysis["reference_product"],
        "observed_competitor_count": analysis["competitor_count"],
        "observed_next_action": analysis["next_action"],
    }


def run_listing_growth_eval() -> dict:
    _operating_unit, _cycle_policy, category_context, product_diagnosis = _build_erp_inferred_context()
    competitor_analysis = build_competitor_analysis(product_diagnosis, category_context)
    plan = build_listing_growth_plan(category_context, competitor_analysis)
    draft = plan["listing_draft"]
    passed = (
        plan["category_name"] == "家居生活商品"
        and plan["data_source"] == "examples/category_home_living/mock_supplier_products.csv"
        and plan["candidate_count"] > 0
        and plan["top_candidate"]["score"] > 0
        and bool(draft["title_draft"])
        and draft["requires_human_approval"] is True
        and draft["auto_publish_allowed"] is False
        and plan["safe_use_policy"].startswith("只生成")
    )
    return {
        "eval_id": "listing_growth_eval_001",
        "passed": passed,
        "observed_top_candidate": plan["top_candidate"],
        "observed_title_draft": draft["title_draft"],
        "observed_next_action": plan["next_action"],
    }


def run_traffic_feedback_eval() -> dict:
    _operating_unit, _cycle_policy, category_context, product_diagnosis = _build_erp_inferred_context()
    competitor_analysis = build_competitor_analysis(product_diagnosis, category_context)
    listing_plan = build_listing_growth_plan(category_context, competitor_analysis)
    report = build_traffic_feedback_report(category_context, listing_plan)
    passed = (
        report["category_name"] == "家居生活商品"
        and report["data_source"] == "examples/category_home_living/mock_traffic_tests.csv"
        and report["experiment_count"] > 0
        and bool(report["decision_summary"])
        and bool(report["loopback_actions"])
        and bool(report["next_action"])
        and report["safe_use_policy"].startswith("只生成")
    )
    return {
        "eval_id": "traffic_feedback_eval_001",
        "passed": passed,
        "observed_decision_summary": report["decision_summary"],
        "observed_next_action": report["next_action"],
        "observed_loopback_actions": report["loopback_actions"],
    }


def run_operating_loop_eval() -> dict:
    datasets = load_all()
    operating_unit, _cycle_policy, category_context, product_diagnosis = _build_erp_inferred_context()
    customer_segmentation = segment_customers(
        customers=datasets["customers"],
        customer_tags=datasets["customer_tags"],
        interactions=datasets["interactions"],
    )
    competitor_analysis = build_competitor_analysis(product_diagnosis, category_context)
    listing_plan = build_listing_growth_plan(category_context, competitor_analysis)
    traffic_report = build_traffic_feedback_report(category_context, listing_plan)
    loop = build_operating_loop_summary(
        category_context=category_context,
        product_diagnosis=product_diagnosis,
        customer_segmentation=customer_segmentation,
        competitor_analysis=competitor_analysis,
        listing_growth_plan=listing_plan,
        traffic_feedback_report=traffic_report,
    )
    passed = (
        loop["category_name"] == "家居生活商品"
        and loop["category_id"] == operating_unit["category_profile_id"]
        and loop["loop_status"] == "closed_loop_mock_ready"
        and bool(loop["next_module"])
        and bool(loop["next_iteration_plan"])
        and loop["manual_review_required"] is True
        and loop["auto_execution_allowed"] is False
        and loop["safe_use_policy"].startswith("完整经营循环")
    )
    return {
        "eval_id": "operating_loop_eval_001",
        "passed": passed,
        "observed_next_module": loop["next_module"],
        "observed_next_iteration_plan": loop["next_iteration_plan"],
    }


def main() -> None:
    results = [
        run_crm_segmentation_eval(),
        run_rpa_task_eval(),
        run_operating_unit_eval(),
        run_category_profile_eval(),
        run_competitor_analysis_eval(),
        run_listing_growth_eval(),
        run_traffic_feedback_eval(),
        run_operating_loop_eval(),
    ]
    output_dir = ROOT_DIR / "evals" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "latest_results.json"
    output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    failed = [item for item in results if not item["passed"]]
    print(json.dumps(results, ensure_ascii=False, indent=2))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
