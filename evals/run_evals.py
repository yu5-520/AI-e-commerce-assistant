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
from src.rag.simple_retriever import retrieve  # noqa: E402
from src.rpa_tasks.generate_task_draft import generate_customer_tasks  # noqa: E402


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


def run_category_profile_eval() -> dict:
    context = build_category_context("sun_protection_clothing")
    profile = context["category_profile"]
    hits = retrieve("防晒服 价格带 季节性 尺码 退换", top_k=3)
    passed = (
        profile["category_name"] == "防晒服"
        and bool(profile["price_bands"])
        and bool(profile["common_return_reasons"])
        and any(hit.get("source") == "category_profiles/sun_protection_clothing.md" for hit in hits)
    )
    return {
        "eval_id": "category_profile_eval_001",
        "passed": passed,
        "observed_category": profile["category_name"],
        "observed_source": profile["source"],
        "rag_sources": [hit.get("source") for hit in hits],
    }


def run_competitor_analysis_eval() -> dict:
    datasets = load_all()
    product_diagnosis = diagnose_products(
        products=datasets["products"],
        orders=datasets["orders"],
        inventory=datasets["inventory"],
        refunds=datasets["refunds"],
    )
    category_context = build_category_context("sun_protection_clothing")
    analysis = build_competitor_analysis(product_diagnosis, category_context)
    passed = (
        analysis["category_name"] == "防晒服"
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


def main() -> None:
    results = [
        run_crm_segmentation_eval(),
        run_rpa_task_eval(),
        run_category_profile_eval(),
        run_competitor_analysis_eval(),
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
