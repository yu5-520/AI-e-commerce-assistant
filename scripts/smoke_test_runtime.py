from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.approval.risk_rules import classify_task  # noqa: E402
from src.rag.simple_retriever import retrieve  # noqa: E402
from src.services.data_import_service import validate_all_imports  # noqa: E402
from src.workflow.mock_workflow import build_mock_workflow_result  # noqa: E402


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    """Smoke-test the current main product workflow.

    The repository used to contain a legacy `backend.server` runtime for a
    PDD-only demo. The product entrypoint is now `src.workflow.mock_workflow`
    and `src.api.main`, so this test intentionally validates the unified
    AI + RPA + ERP + CRM workflow instead of the archived legacy backend.
    """
    validation = validate_all_imports()
    assert_true(validation["status"] == "passed", "mock ERP / CRM datasets should pass validation")
    assert_true(validation["failed_count"] == 0, "mock import validation should have no failed checks")
    assert_true(len(validation["datasets"]) >= 7, "validation should cover ERP and CRM mock datasets")

    result = build_mock_workflow_result(write_outputs=False, record_logs=False)
    summary = result.get("summary") or {}
    assert_true(result.get("workflow_mode") == "Workflow-first", "workflow should stay Workflow-first")
    assert_true(summary.get("product_count", 0) > 0, "workflow should diagnose products")
    assert_true(summary.get("customer_count", 0) > 0, "workflow should segment customers")
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

    rag_hits = retrieve("活动价 保本线 利润 风险", top_k=3)
    assert_true(isinstance(rag_hits, list), "RAG retriever should return a list")

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
