"""Run the mock ERP-based operating unit ecommerce workflow demo.

Usage:
    python -m src.run_demo

This CLI uses the same workflow service as FastAPI. Product logic now starts
from ERP product data, infers the operating unit, chooses the cycle policy, and
then runs category context, competitor, listing, traffic feedback, and loop
summary nodes.
"""

from __future__ import annotations

from src.workflow.mock_workflow import build_mock_workflow_result


def main() -> None:
    result = build_mock_workflow_result(write_outputs=True)
    summary = result["summary"]
    competitor_analysis = result.get("competitor_analysis") or {}
    reference_product = competitor_analysis.get("reference_product") or {}
    listing_growth_plan = result.get("listing_growth_plan") or {}
    top_candidate = listing_growth_plan.get("top_candidate") or {}

    print("Mock workflow completed.")
    print(f"Operating unit: {summary.get('unit_name')} ({summary.get('operating_unit_id')})")
    print(f"Cycle policy: {summary.get('cycle_frequency')} / {summary.get('cycle_type')}")
    print(f"Category context: {summary.get('category_name')} ({summary.get('category_id')})")
    print(f"Product diagnosis count: {summary['product_count']}")
    print(f"Customer segmentation count: {summary['customer_count']}")
    print(f"Competitor count: {summary.get('competitor_count')}")
    print(f"Competitor trigger product: {reference_product.get('product_id')} - {reference_product.get('product_name')}")
    print(f"Listing candidate count: {summary.get('listing_candidate_count')}")
    print(f"Top listing candidate: {top_candidate.get('supplier_product_id')} - {top_candidate.get('product_name')}")
    print(f"Traffic experiment count: {summary.get('traffic_experiment_count')}")
    print(f"Traffic next action: {summary.get('traffic_next_action')}")
    print(f"Loop status: {summary.get('loop_status')}")
    print(f"Loop next module: {summary.get('loop_next_module')}")
    print(f"RPA task draft count: {summary['rpa_task_count']}")
    print(f"Approval required count: {summary['approval_required_count']}")
    print(f"Report generated: {result.get('report_path')}")


if __name__ == "__main__":
    main()
