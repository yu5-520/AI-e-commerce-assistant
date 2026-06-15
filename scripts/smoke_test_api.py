"""API smoke test for the current AI ERP operating advisor product surface.

Run from repository root:
    python scripts/smoke_test_api.py

The script uses FastAPI TestClient, so it does not need a running uvicorn
process. It intentionally checks only current product-critical API contracts.
Legacy demo/debug routes are not tested because they are no longer mounted.
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

    today = assert_status("GET", "/api/business/today")
    assert_keys(today, ["page_title", "priority", "operating_unit", "cycle", "cards", "boundaries", "raw"], "business today")
    assert today["operating_unit"]["name"] == "家居生活商品", "business today should expose ERP-inferred operating unit"
    assert today["cycle"]["frequency_label"] == "每天", "business today should expose readable cycle frequency"

    operating_unit = assert_status("GET", "/api/business/operating-unit")
    assert_keys(operating_unit, ["unit_name", "unit_id", "source", "cycle_policy"], "operating unit")
    assert operating_unit["unit_id"] == "home_living_goods", "operating unit should be inferred from ERP mock data"

    data_health = assert_status("GET", "/api/business/data-health")
    assert_keys(data_health, ["status", "summary", "datasets", "message"], "business data health")

    products = assert_status("GET", "/api/business/products")
    assert_keys(products, ["title", "summary", "items"], "business products")
    assert products["items"], "business products should contain product cards"

    competitors = assert_status("GET", "/api/business/competitors")
    assert_keys(competitors, ["title", "category_name", "competitor_count", "opportunity_actions", "next_action"], "business competitors")
    assert competitors["competitor_count"] > 0, "competitors should contain same-operating-unit references"

    listing = assert_status("GET", "/api/business/listing")
    assert_keys(listing, ["title", "candidate_count", "top_candidate", "title_draft", "image_plan", "sku_plan"], "business listing")
    assert listing["title_draft"], "listing should include a draft title"

    traffic = assert_status("GET", "/api/business/traffic")
    assert_keys(traffic, ["title", "experiment_count", "next_action", "loopback_actions", "items"], "business traffic")
    assert traffic["experiment_count"] > 0, "traffic should contain experiments"

    actions = assert_status("GET", "/api/business/actions")
    assert_keys(actions, ["items"], "business actions")
    assert actions["items"], "actions should include confirmation items"

    action_id = actions["items"][0]["action_id"]
    approved = assert_status("POST", f"/api/approvals/{action_id}/approve")
    assert approved["approval_status"] == "approved", "approval status should be approved"

    rejected = assert_status("POST", f"/api/approvals/{action_id}/reject")
    assert rejected["approval_status"] == "rejected", "approval status should be rejected"

    approval_records = assert_status("GET", "/api/approvals/records")
    assert isinstance(approval_records, list), "approval records should be a list"

    report_text = assert_status("GET", "/api/business/report")
    assert isinstance(report_text, str) and report_text.strip(), "business report should not be empty"

    final_db_status = assert_status("GET", "/api/system/db-status")
    assert final_db_status["summary"]["total_records"] >= 1, "db should contain records after smoke test"

    print("API smoke test passed.")


if __name__ == "__main__":
    run_smoke_test()
