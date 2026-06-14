"""Product-oriented service functions built on top of the mock workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from src.workflow.mock_workflow import build_mock_workflow_result

ROOT_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT_DIR / "outputs"


def run_full_workflow(write_outputs: bool = True) -> Dict[str, Any]:
    """Run full mock workflow and return structured result."""
    return build_mock_workflow_result(write_outputs=write_outputs)


def get_products() -> List[Dict[str, Any]]:
    """Return product diagnosis records as product summary cards for MVP."""
    return run_full_workflow(write_outputs=False)["product_diagnosis"]


def get_product(product_id: str) -> Optional[Dict[str, Any]]:
    """Return one product diagnosis record by product_id."""
    return next((item for item in get_products() if item.get("product_id") == product_id), None)


def get_customers() -> List[Dict[str, Any]]:
    """Return customer segmentation records as customer summary cards for MVP."""
    return run_full_workflow(write_outputs=False)["customer_segmentation"]


def get_customer(customer_id: str) -> Optional[Dict[str, Any]]:
    """Return one customer segmentation record by customer_id."""
    return next((item for item in get_customers() if item.get("customer_id") == customer_id), None)


def get_tasks() -> List[Dict[str, Any]]:
    """Return generated RPA task drafts."""
    return run_full_workflow(write_outputs=False)["rpa_tasks"]


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """Return one task draft by task_id."""
    return next((item for item in get_tasks() if item.get("task_id") == task_id), None)


def get_approval_required_tasks() -> List[Dict[str, Any]]:
    """Return tasks that require manual approval."""
    return run_full_workflow(write_outputs=False)["approval_required_tasks"]


def get_demo_report_text() -> str:
    """Return latest Markdown report, generating it if necessary."""
    report_path = OUTPUT_DIR / "demo_report.md"
    if not report_path.exists():
        run_full_workflow(write_outputs=True)
    return report_path.read_text(encoding="utf-8")
