from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.approval.risk_rules import classify_task  # noqa: E402
from src.category import build_category_context  # noqa: E402
from src.rag.simple_retriever import retrieve  # noqa: E402
from src.services.data_import_service import validate_all_imports  # noqa: E402
from src.workflow.mock_workflow import build_mock_workflow_result  # noqa: E402


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    """Smoke-test the current main product workflow.

    The product entrypoint is `src.workflow.mock_workflow` and `src.api.main`.
    This test validates the V0.8 ERP / CRM workflow, the V0.9 vertical category
    profile hook, the V1.0 same-category competitor analysis skeleton, the V1.1
    listing growth plan skeleton, and the V1.2 traffic feedback loop skeleton.
    """
    validation = validate_all_imports()
    assert_true(validation["status"] == "passed", "mock ERP / CRM datasets should pass validation")
    assert_true(validation["failed_count"] == 0, "mock import validation should have no failed checks")
    assert_true(len(validation["datasets"]) >= 7, "validation should cover ERP and CRM mock datasets")

    standalone_category_context = build_category_context("sun_protection_clothing")
    assert_true(
        standalone_category_context["category_profile"]["category_name"] == "防晒服",
        "category context should load the sun protection clothing profile",
    )
    assert_true(
        "价格带" in " ".join(standalone_category_context["category_rules"]["risk_focus"]),
        "category risk rules should include category-specific risk focus",
    )

    result = build_mock_workflow_result(write_outputs=False, record_logs=False)
    summary = result.get("summary") or {}
    category_context = result.get("category_context") or {}
    category_profile = category_context.get("category_profile") or {}
    competitor_analysis = result.get("competitor_analysis") or {}
    listing_growth_plan = result.get("listing_growth_plan") or {}
    listing_draft = listing_growth_plan.get("listing_draft") or {}
    traffic_feedback_report = result.get("traffic_feedback_report") or {}

    assert_true(result.get("workflow_mode") == "Workflow-first", "workflow should stay Workflow-first")
    assert_true(category_profile.get("category_id") == "sun_protection_clothing", "workflow should inject category context")
    assert_true(summary.get("category_name") == "防晒服", "workflow summary should expose category name")
    assert_true(summary.get("product_count", 0) > 0, "workflow should diagnose products")
    assert_true(summary.get("customer_count", 0) > 0, "workflow should segment customers")
    assert_true(summary.get("competitor_count", 0) > 0, "workflow should compare same-category competitors")
    assert_true(competitor_analysis.get("analysis_id"), "workflow should return competitor analysis")
    assert_true(
        competitor_analysis.get("data_source") == "examples/category_sun_protection/mock_competitors.csv",
        "competitor analysis should use the mock competitor dataset",
    )
    assert_true(
        competitor_analysis.get("reference_product", {}).get("trigger_reason"),
        "competitor analysis should explain why it was triggered",
    )
    assert_true(
        competitor_analysis.get("safe_use_policy"),
        "competitor analysis should include safe-use policy",
    )
    assert_true(summary.get("listing_candidate_count", 0) > 0, "workflow should score listing candidates")
    assert_true(
        listing_growth_plan.get("data_source") == "examples/category_sun_protection/mock_supplier_products.csv",
        "listing growth should use the mock supplier product dataset",
    )
    assert_true(
        listing_growth_plan.get("top_candidate", {}).get("score", 0) > 0,
        "listing growth should choose a scored top candidate",
    )
    assert_true(listing_draft.get("requires_human_approval") is True, "listing draft should require human approval")
    assert_true(listing_draft.get("auto_publish_allowed") is False, "listing draft must not auto-publish")
    assert_true(listing_growth_plan.get("safe_use_policy"), "listing growth should include safe-use policy")
    assert_true(summary.get("traffic_experiment_count", 0) > 0, "workflow should diagnose traffic experiments")
    assert_true(
        traffic_feedback_report.get("data_source") == "examples/category_sun_protection/mock_traffic_tests.csv",
        "traffic feedback should use the mock traffic test dataset",
    )
    assert_true(traffic_feedback_report.get("decision_summary"), "traffic feedback should summarize next-action decisions")
    assert_true(traffic_feedback_report.get("loopback_actions"), "traffic feedback should produce loopback actions")
    assert_true(traffic_feedback_report.get("safe_use_policy"), "traffic feedback should include safe-use policy")
    assert_true(summary.get("rpa_task_count", 0) > 0, "workflow should generate RPA task drafts")
    assert_true(summary.get("auto_execution_allowed_count") == 0, "MVP must not allow automatic execution")

    tasks = result.get("rpa_tasks") or []
    assert_true(tasks, "workflow should return task drafts")
    for task in tasks:
        assert_true(task.get("requires_approval") is True, f"task {task.get('task_id')} should require approval")
        assert_true(task.get("auto_execution_allowed") is False, f"task {task.get('task_id')} should not auto-execute")
        assert_true(task.get("policy_reason"), f"task {task.get('task_id')} should include policy_reason")

    high_risk_policy = classify_task("auto_price_change")
    assert_true(high_risk_policy["risk_level"] == "high", "auto price change should be high risk")
    assert_true(high_risk_policy["auto_execution_allowed"] is False, "high risk tasks should not auto-execute")

    rag_hits = retrieve("防晒服 价格带 季节性 尺码 退换", top_k=3)
    assert_true(isinstance(rag_hits, list), "RAG retriever should return a list")
    assert_true(
        any("category_profiles/sun_protection_clothing.md" == hit.get("source") for hit in rag_hits),
        "RAG retriever should include category profile documents",
    )

    print(
        json.dumps(
            {
                "ok": True,
                "workflow": result.get("workflow_name"),
                "summary": summary,
                "validation_status": validation["status"],
                "task_count": len(tasks),
                "rag_hit_count": len(rag_hits),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
