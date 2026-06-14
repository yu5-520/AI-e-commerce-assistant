"""Run the mock vertical shelf ecommerce workflow demo.

Usage:
    python -m src.run_demo

V1.0 note:
    The CLI and FastAPI API share the same workflow service in
    src.workflow.mock_workflow. The workflow now loads a vertical category
    profile and same-category competitor analysis before RPA task drafting.
"""

from __future__ import annotations

from src.workflow.mock_workflow import build_mock_workflow_result


def main() -> None:
    result = build_mock_workflow_result(write_outputs=True)
    summary = result["summary"]
    competitor_analysis = result.get("competitor_analysis") or {}
    reference_product = competitor_analysis.get("reference_product") or {}

    print("Mock workflow completed.")
    print(f"Category: {summary.get('category_name')} ({summary.get('category_id')})")
    print(f"Product diagnosis count: {summary['product_count']}")
    print(f"Customer segmentation count: {summary['customer_count']}")
    print(f"Competitor count: {summary.get('competitor_count')}")
    print(f"Competitor trigger product: {reference_product.get('product_id')} - {reference_product.get('product_name')}")
    print(f"RPA task draft count: {summary['rpa_task_count']}")
    print(f"Approval required count: {summary['approval_required_count']}")
    print(f"Report generated: {result.get('report_path')}")


if __name__ == "__main__":
    main()
