"""API smoke test for the current AI ERP operating advisor V4.3 product surface.

Run from repository root:
    python scripts/smoke_test_api.py

The script uses FastAPI TestClient, so it does not need a running uvicorn
process. It checks modular routes, account roles, task reports, V3 report
alerts, V4 module agents, V4.1 RAG memory, V4.2 task agents, V4.3 creative vertical Agent,
and the dispatch / accept / submit / review flow.
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
    assert health["v4_module_agent_layer"] is True, "V4 module agent runtime should be exposed"
    assert health["agent_requires_human_confirmation"] is True, "Agent output must require human confirmation"
    assert health["v410_rag_memory"] is True, "V4.1 RAG memory runtime should be exposed"
    assert health["v420_task_generation_agent"] is True, "V4.2 task generation Agent should be exposed"
    assert health["task_playbook_agent"] is True, "V4.2 task playbook Agent should be exposed"
    assert health["v430_creative_vertical_agent"] is True, "V4.3 creative vertical Agent should be exposed"

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

    agents = assert_status("GET", "/api/modules/agents")
    assert_keys(agents, ["version", "agents", "boundary", "forbiddenActions"], "module agents")
    assert str(agents["version"]).startswith("4."), "Agent registry should be V4"
    assert len(agents["agents"]) >= 7, "V4 should expose the seven module agents"

    product_agent = assert_status("GET", "/api/modules/agents/product/P001")
    assert_keys(product_agent, ["agentId", "summary", "evidence", "suggestions", "taskDrafts", "forbiddenActions"], "product agent")
    assert product_agent["taskDrafts"], "product agent should produce task drafts"
    assert "不直接改价" in product_agent["forbiddenActions"], "Agent must expose forbidden actions"

    cycle_agent = assert_status("GET", "/api/modules/agents/cycle/日报")
    assert_keys(cycle_agent, ["agentName", "summary", "humanDecision", "forbiddenActions"], "cycle agent")

    rag_summary = assert_status("GET", "/api/modules/rag-memory")
    assert_keys(rag_summary, ["version", "total", "approved", "pendingReview", "levels"], "RAG memory summary")
    assert rag_summary["approved"] >= 1, "RAG memory should seed approved playbooks"

    rag_search = assert_status("GET", "/api/modules/rag-memory/search?problem_type=low_roi_high_refund&category_id=home_living_goods")
    assert_keys(rag_search, ["version", "items", "retrievalRule"], "RAG memory search")
    assert rag_search["items"], "RAG memory should retrieve seeded low ROI playbook"

    generated = assert_post_json(
        "/api/modules/agents/tasks/generate",
        {"sourceModule": "traffic", "entityId": "T001", "autoCreate": False},
    )
    assert_keys(generated, ["agentName", "candidates", "retrieval", "boundary"], "V4.2 task generation")
    assert generated["candidates"], "task generation should return candidates"
    assert generated["candidates"][0]["ragReferences"], "task generation should cite RAG references"
    assert generated["candidates"][0]["taskDraft"]["taskType"] == "V4.2 RAG任务生成", "task draft should carry V4.2 identity"

    creative = assert_post_json(
        "/api/modules/agents/creative/P002",
        {"taskGoal": "提升点击率并降低安装预期退款", "platform": "拼多多", "categoryId": "home_living_goods"},
    )
    assert_keys(creative, ["agentName", "categoryProfile", "platformRule", "titleVariants", "mainImageDirections", "sellingPointOrder", "testPlan", "taskDraft", "forbiddenActions"], "V4.3 creative vertical agent")
    assert creative["agentName"] == "标题主图垂直类目 Agent", "creative agent should identify itself"
    assert len(creative["titleVariants"]) >= 3, "creative agent should generate title variants"
    assert len(creative["mainImageDirections"]) >= 3, "creative agent should generate main-image directions"
    assert creative["taskDraft"]["taskType"] == "V4.3 垂直类目创意测试", "creative task draft should carry V4.3 identity"
    assert "不直接发布商品" in creative["forbiddenActions"], "creative agent must not publish products"

    todo_reset = assert_status("POST", "/api/modules/todo/reset")
    assert_keys(todo_reset, ["tasks", "logs"], "todo reset")

    todo = assert_status("GET", "/api/modules/todo")
    assert_keys(todo, ["tasks", "activeTasks", "scope"], "todo")
    assert todo["activeTasks"], "todo should expose active task pool"
    task_id = todo["activeTasks"][0]["id"]

    playbook = assert_status("GET", f"/api/modules/agents/tasks/{task_id}/playbook")
    assert_keys(playbook, ["agentName", "recommendedStyle", "strategies", "evidenceToSubmit", "ragReferences"], "V4.2 task playbook")
    assert len(playbook["strategies"]) >= 3, "playbook should expose multiple operating styles"

    task_report = assert_status("GET", f"/api/modules/task-reports/tasks/{task_id}")
    assert_keys(task_report, ["reportType", "title", "evidence", "suggestedActions", "relatedTask"], "task report")

    task_agent = assert_status("GET", f"/api/modules/agents/task/{task_id}?mode=breakdown")
    assert task_agent["taskDrafts"], "task breakdown agent should produce task drafts"

    feedback_draft = assert_post_json(
        f"/api/modules/rag-memory/feedback/tasks/{task_id}",
        {
            "operatorSubmission": "已先查售后，复查详情页承诺和客服话术。",
            "managerReview": "通过，可沉淀为低 ROI 高退款处理案例。",
            "beforeMetrics": {"roi": "0.9", "refundRate": "8.4%"},
            "afterMetrics": {"roi": "1.4", "refundRate": "5.2%"},
        },
    )
    assert feedback_draft["experienceCard"]["sourceTaskId"] == task_id, "feedback agent should produce an experience card"
    assert feedback_draft["needsHumanReviewBeforeWrite"] is True, "RAG write should require human review"

    case_id = feedback_draft["experienceCard"]["caseId"]
    approved_case = assert_post_json(f"/api/modules/rag-memory/cases/{case_id}/approve", {"reason": "smoke test approval"})
    assert approved_case["case"]["status"] == "approved", "owner / manager should approve experience card"

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
