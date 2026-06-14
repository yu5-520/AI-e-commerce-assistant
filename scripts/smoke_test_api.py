"""API smoke test for the product workbench.

Run from repository root:
    python scripts/smoke_test_api.py

The script uses FastAPI TestClient, so it does not need a running uvicorn
process. It intentionally checks only product-critical API contracts, not deep
business correctness.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def assert_status(method: str, path: str, expected_status: int = 200) -> Any:
    response = client.request(method, path)
    assert response.status_code == expected_status, (
        f"{method} {path} expected {expected_status}, got {response.status_code}: {response.text}"
    )
    if response.headers.get("content-type", "").startswith("application/json"):
        return response.json()
    return response.text


def assert_keys(payload: Dict[str, Any], keys: list[str], name: str) -> None:
    missing = [key for key in keys if key not in payload]
    assert not missing, f"{name} missing keys: {missing}"


def run_smoke_test() -> None:
    health = assert_status("GET", "/api/health")
    assert_keys(health, ["ok", "version", "mode", "safety"], "health")
    assert health["ok"] is True, "health.ok should be true"

    db_status = assert_status("GET", "/api/system/db-status")
    assert_keys(db_status, ["ok", "database", "tables", "summary"], "db_status")

    clear_guard = client.post("/api/system/clear-demo-data")
    assert clear_guard.status_code == 400, "clear-demo-data must require confirm=true"

    validation = assert_status("POST", "/api/data/validate")
    assert_keys(validation, ["status", "datasets", "relationship_checks"], "data validation")

    import_record = assert_status("POST", "/api/data/import/mock")
    assert_keys(import_record, ["import_id", "workflow_run_id", "status", "validation"], "import record")

    imports = assert_status("GET", "/api/data/imports")
    assert isinstance(imports, list), "imports should be a list"

    demo = assert_status("GET", "/api/demo/run")
    assert_keys(demo, ["workflow_name", "summary", "rpa_tasks", "workflow_run_id"], "demo run")
    assert demo["rpa_tasks"], "demo run should generate at least one task"

    task_id = demo["rpa_tasks"][0]["task_id"]
    approved = assert_status("POST", f"/api/approvals/{task_id}/approve")
    assert approved["approval_status"] == "approved", "approval status should be approved"

    rejected = assert_status("POST", f"/api/approvals/{task_id}/reject")
    assert rejected["approval_status"] == "rejected", "approval status should be rejected"

    approval_records = assert_status("GET", "/api/approvals/records")
    assert isinstance(approval_records, list), "approval records should be a list"

    tasks = assert_status("GET", "/api/tasks")
    assert isinstance(tasks, list), "tasks should be a list"

    reports = assert_status("GET", "/api/reports")
    assert "reports" in reports, "reports payload should contain reports"

    report_text = assert_status("GET", "/api/reports/demo")
    assert isinstance(report_text, str) and report_text.strip(), "demo report should not be empty"

    workflow_runs = assert_status("GET", "/api/logs/workflow-runs?limit=5&status=success")
    assert_keys(workflow_runs, ["items", "total", "limit", "offset", "filters"], "workflow run logs")

    execution_logs = assert_status("GET", "/api/logs/execution-logs?limit=5")
    assert_keys(execution_logs, ["items", "total", "limit", "offset", "filters"], "execution logs")

    filtered_runs = assert_status("GET", "/api/logs/workflow-runs?limit=5&workflow_type=full_mock_workflow")
    assert_keys(filtered_runs, ["items", "total", "filters"], "filtered workflow runs")

    if workflow_runs["items"]:
        run_id = workflow_runs["items"][0]["workflow_run_id"]
        run_logs = assert_status("GET", f"/api/logs/workflow-runs/{run_id}/execution-logs?limit=10")
        assert_keys(run_logs, ["items", "total", "workflow_run_id"], "logs by run")

    final_db_status = assert_status("GET", "/api/system/db-status")
    assert final_db_status["summary"]["total_records"] >= 1, "db should contain records after smoke test"

    print("API smoke test passed.")


if __name__ == "__main__":
    run_smoke_test()
