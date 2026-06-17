"""API smoke test for the current AI ERP operating advisor v3 product surface.

Run from repository root:
    python scripts/smoke_test_api.py

The script uses FastAPI TestClient, so it does not need a running uvicorn
process. It checks modular routes, account roles, task reports, V3 report
alerts, and the dispatch / accept / submit / review flow.
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


def assert_post_json(path: str, payload: Dict[str, Any], expected_status: int = 200) -> Any:
    response = client.post(path, json=payload)
    assert response.status_code == expected_status, (
        f"POST {path} expected {expected_status}, got {response.status_code}: {response.text}"
    )
    if response.headers.get("content-type", "").startswith("application/json"):
        return response.json()
    return response.text


def assert_keys(payload: Dict[str, Any], keys: list[str], name: str) -> None:
    missing = [key for key in keys if key not in payload]
    assert not missing, f"{name} missing keys: {missing}"


def run_smoke_test() -> None:
    health = assert_status("GET", "/api/health")
    assert_keys(health, ["ok", "version", "product", "mode", "safety", "account_entry"], "health")
    assert health["ok"] is True, "health.ok should be true"
    assert health["version"] == app.version, "health.version should match FastAPI app version"
    assert health["api_entry"] == "/api/modules/*", "active API entry should be modular"
    assert health["account_entry"] == "/api/accounts", "account entry should be exposed"
    assert health["v3_report_alert_event"] is True, "V3 report alert runtime should be exposed"

    db_status = assert_status("GET", "/api/system/db-status")
    assert_keys(db_status, ["ok", "database", "tables", "summary"], "db_status")
    table_names = {item["table_name"] for item in db_status["tables"]}
    assert "task_status" in table_names, "db should keep task status table"

    clear_guard = client.post("/api/system/clear-demo-data")
    assert clear_guard.status_code == 400, "clear-demo-data must require confirm=true"

    clear_runtime_guard = client.post("/api/system/clear-runtime-data")
    assert clear_runtime_guard.status_code == 400, "clear-runtime-data must require confirm=true"

    validation = assert_status("POST", "/api/data/validate")
    assert_keys(validation, ["status", "datasets", "relationship_checks"], "data validation")

    import_record = assert_status("POST", "/api/data/import/mock")
    assert_keys(import_record, ["import_id", "workflow_run_id", "status", "validation"], "import record")

    v3_import = assert_post_json("/api/data/import/mock-alerts", {})
    assert_keys(v3_import, ["version", "datasetCount", "alertCount", "createdTaskCount", "summary"], "v3 import")
    assert v3_import["version"] == "3.0.0", "v3 import should report version 3.0.0"

    v3_summary = assert_status("GET", "/api/data/v3-summary")
    assert_keys(v3_summary, ["version", "activeAlertCount", "latestDataVersion", "globalSyncTargets"], "v3 summary")

    v3_alerts = assert_status("GET", "/api/data/alerts")
    assert isinstance(v3_alerts, list), "v3 alerts should be a list"

    imports = assert_status("GET", "/api/data/imports")
    assert isinstance(imports, list), "imports should be a list"

    accounts = assert_status("GET", "/api/accounts")
    assert_keys(accounts, ["currentUser", "roles", "permissions", "users", "stores", "taskFlow"], "accounts")
    role_names = {role["name"] for role in accounts["roles"]}
    assert {"老板账号", "店群总管账号", "运营账号", "数据 / 财务账号", "只读观察账号"}.issubset(role_names), "roles should be present"

    me = assert_status("GET", "/api/accounts/me")
    assert me["roleName"] == "老板账号", "mock current user should be owner"

    dashboard = assert_status("GET", "/api/modules/dashboard")
    assert_keys(dashboard, ["tasks", "api_entry", "service", "v3", "data_refresh"], "modules dashboard")
    assert dashboard["api_entry"] == "/api/modules/dashboard"

    operating_unit = assert_status("GET", "/api/modules/operating-unit")
    assert operating_unit, "operating unit route should return payload"

    products = assert_status("GET", "/api/modules/product")
    assert isinstance(products, list) and products, "product module should return cards"
    assert "suggestedTaskKey" in products[0], "product cards should carry backend task identity"
    assert "alertState" in products[0], "product cards should expose V3 alert state"

    competitors = assert_status("GET", "/api/modules/competitor")
    assert isinstance(competitors, list), "competitor module should return list"

    listing = assert_status("GET", "/api/modules/listing")
    assert isinstance(listing, list), "listing module should return list"

    traffic = assert_status("GET", "/api/modules/traffic")
    assert isinstance(traffic, list), "traffic module should return list"
    if traffic:
        assert "alertState" in traffic[0], "traffic cards should expose V3 alert state"

    report = assert_status("GET", "/api/modules/report")
    assert_keys(report, ["reportGroups", "reportDetails", "v3", "recentAlerts"], "report module")

    todo_reset = assert_status("POST", "/api/modules/todo/reset")
    assert_keys(todo_reset, ["tasks", "logs"], "todo reset")

    todo = assert_status("GET", "/api/modules/todo")
    assert_keys(todo, ["tasks", "activeTasks", "scope"], "todo")
    assert todo["activeTasks"], "todo should expose active task pool"
    task_id = todo["activeTasks"][0]["id"]

    task_report = assert_status("GET", f"/api/modules/task-reports/tasks/{task_id}")
    assert_keys(task_report, ["reportType", "title", "evidence", "suggestedActions", "relatedTask"], "task report")

    assigned = assert_post_json(
        f"/api/modules/todo/{task_id}/assign",
        {"assignee_id": "U003", "reviewer_id": "U002", "operator_id": "U002", "note": "smoke test assignment"},
    )
    assert assigned["status"] in {"待接收", "处理中"}, "assigned task should be waiting accept or processing"
    assert assigned["assigneeId"] == "U003", "assigned task should target operator account"

    accepted = assert_post_json(
        f"/api/modules/todo/{task_id}/accept",
        {"note": "smoke test accept"},
    )
    assert accepted["status"] == "处理中", "accepted task should enter processing status"

    submitted = assert_post_json(
        f"/api/modules/todo/{task_id}/submit",
        {"submitter_id": "U003", "note": "smoke test submission"},
    )
    assert submitted["status"] == "待复核", "submitted task should enter review status"

    returned = assert_post_json(
        f"/api/modules/todo/{task_id}/review",
        {"reviewer_id": "U002", "decision": "return", "note": "need more evidence"},
    )
    assert returned["workflowStatus"] == "已退回", "returned task should keep active workflow"

    submitted_again = assert_post_json(
        f"/api/modules/todo/{task_id}/submit",
        {"submitter_id": "U003", "note": "second submission"},
    )
    assert submitted_again["status"] == "待复核", "task should be submittable again after return"

    approved = assert_post_json(
        f"/api/modules/todo/{task_id}/review",
        {"reviewer_id": "U002", "decision": "approve", "note": "approved"},
    )
    assert approved["status"] == "已完成", "approved task should complete"
    assert approved["workflowStatus"] == "已归档", "approved task should archive workflow"

    active_after_review = assert_status("GET", "/api/modules/todo")
    assert task_id not in {task["id"] for task in active_after_review["activeTasks"]}, "approved task should leave active todo"

    logs = assert_status("GET", "/api/modules/log")
    assert isinstance(logs, list) and logs, "log module should include task workflow logs"

    final_db_status = assert_status("GET", "/api/system/db-status")
    assert final_db_status["summary"]["table_count"] >= 6, "db should expose runtime tables"

    print("API smoke test passed.")


if __name__ == "__main__":
    run_smoke_test()
