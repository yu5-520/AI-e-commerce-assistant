"""API smoke test for the current AI ERP operating advisor V4.5 product surface.

Run from repository root:
    python scripts/smoke_test_api.py

This smoke test checks the current product trunk: Agent registry, problem-type
ActionPlans, LLM Gateway, Tool Gateway, MCP adapter boundary, creative LLM
enrichment fallback, feedback flywheel, and task lifecycle.
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


def assert_action_plan(payload: Dict[str, Any], name: str) -> None:
    assert_keys(payload, ["actionPlan", "executionPackages", "executionSteps", "evidenceRequired", "acceptanceCriteria"], name)
    assert payload["actionPlan"]["problemType"], f"{name} should expose problem type"
    assert payload["executionPackages"], f"{name} should expose targeted execution packages"
    assert payload["executionSteps"], f"{name} should expose operator actions"


def run_smoke_test() -> None:
    health = assert_status("GET", "/api/health")
    assert_keys(health, ["ok", "version", "product", "mode", "safety", "account_entry", "llm_entry"], "health")
    assert health["ok"] is True
    assert health["version"] == app.version
    assert health["api_entry"] == "/api/modules/*"
    assert health["v450_llm_gateway"] is True
    assert health["v450_tool_gateway"] is True
    assert health["v450_mcp_adapter_boundary"] is True
    assert health["v442_problem_type_action_plan"] is True
    assert health["feedback_requires_human_approval"] is True

    llm_status = assert_status("GET", "/api/llm/status")
    assert_keys(llm_status, ["llm", "guardrail", "prompts", "toolGateway", "mcpAdapter", "trace"], "llm status")
    assert llm_status["llm"]["providerName"], "LLM Gateway should expose provider selection"
    assert "change_price" in llm_status["toolGateway"]["blockedTools"]
    assert llm_status["mcpAdapter"]["enabled"] is False

    manual_llm = assert_post_json(
        "/api/llm/generate",
        {"promptName": "creative_test_package", "payload": {"productFacts": {"shortName": "厨房置物架"}}, "expectedKeys": ["llmSummary", "titleVariants", "mainImageDirections", "riskCheck"]},
    )
    assert_keys(manual_llm, ["version", "provider", "model", "status", "fallbackUsed", "output"], "manual llm")
    assert manual_llm["output"]["llmGuardrail"]["valid"] is True

    blocked_tool = assert_post_json("/api/llm/tools/change_price", {"productId": "P001", "price": 99})
    assert blocked_tool["blocked"] is True
    safe_tool = assert_post_json("/api/llm/tools/get_product_snapshot", {"productId": "P001"})
    assert safe_tool["ok"] is True

    db_status = assert_status("GET", "/api/system/db-status")
    assert "task_status" in {item["table_name"] for item in db_status["tables"]}

    accounts = assert_status("GET", "/api/accounts")
    assert_keys(accounts, ["currentUser", "roles", "permissions", "users", "stores", "taskFlow"], "accounts")

    for path in ["/api/modules/dashboard", "/api/modules/operating-unit", "/api/modules/product", "/api/modules/competitor", "/api/modules/listing", "/api/modules/traffic", "/api/modules/report", "/api/modules/log"]:
        payload = assert_status("GET", path)
        assert payload is not None, f"{path} should return payload"

    agents = assert_status("GET", "/api/modules/agents")
    assert_keys(agents, ["version", "agents", "boundary", "forbiddenActions", "v45Endpoints", "v442ActionPlan", "v450LlmGateway"], "module agents")
    assert agents["version"] == app.version, "Agent registry should align with FastAPI version"
    agent_ids = {item.get("id") for item in agents["agents"]}
    assert {"llm-gateway", "tool-gateway", "mcp-adapter", "problem-type-action-plan", "task-generation", "task-playbook", "creative-vertical", "feedback-flywheel"}.issubset(agent_ids)

    product_agent = assert_status("GET", "/api/modules/agents/product/P002")
    assert_keys(product_agent, ["agentId", "summary", "evidence", "suggestions", "taskDrafts", "forbiddenActions", "actionPlan", "executionPackages"], "product agent")
    assert_action_plan(product_agent["taskDrafts"][0], "product task draft")

    generated = assert_post_json("/api/modules/agents/tasks/generate", {"sourceModule": "traffic", "entityId": "T001", "autoCreate": False})
    candidate = generated["candidates"][0]
    assert candidate["taskDraft"]["taskType"] == "V4.4.2 问题类型处理包"
    assert_action_plan(candidate["taskDraft"], "generated task draft")

    creative = assert_post_json(
        "/api/modules/agents/creative/P002",
        {"taskGoal": "提升点击率并降低安装预期退款", "platform": "拼多多", "categoryId": "home_living_goods"},
    )
    assert creative["agentName"] == "标题主图垂直类目 Agent"
    assert len(creative["testPackages"]) >= 3
    assert_keys(creative, ["llmEnrichment", "llmTitleVariants", "llmMainImageDirections", "llmPackagePreviews"], "creative llm enrichment")
    assert creative["llmEnrichment"]["output"]["llmGuardrail"]["valid"] is True

    creative_task = assert_post_json(
        "/api/modules/agents/creative/P002/tasks",
        {"packageIndex": 1, "taskGoal": "测试标题主图点击率", "platform": "拼多多", "categoryId": "home_living_goods"},
    )
    assert creative_task["task"]["selectedPackage"]["packageName"].startswith("方案 B")
    assert creative_task["agent"]["llmEnrichment"], "created creative task should include enriched Agent snapshot"

    feedback = assert_status("GET", "/api/modules/feedback-flywheel")
    assert_keys(feedback, ["agentName", "chain", "memorySummary", "agentEvalMetrics", "learningCandidates", "forbiddenActions"], "feedback flywheel")
    assert "不自动批准经验入库" in feedback["forbiddenActions"]

    todo_reset = assert_status("POST", "/api/modules/todo/reset")
    assert_keys(todo_reset, ["tasks", "logs"], "todo reset")
    todo = assert_status("GET", "/api/modules/todo")
    task_id = todo["activeTasks"][0]["id"]

    task_agent = assert_status("GET", f"/api/modules/agents/task/{task_id}?mode=breakdown")
    assert_keys(task_agent, ["actionPlan", "executionPackages", "taskDrafts", "suggestions"], "module task agent")
    assert_action_plan(task_agent["taskDrafts"][0], "task agent draft")

    task_playbook = assert_status("GET", f"/api/modules/agents/tasks/{task_id}/playbook")
    assert len(task_playbook["strategies"]) >= 3
    assert task_playbook["executionPackages"]

    feedback_draft = assert_post_json(
        f"/api/modules/rag-memory/feedback/tasks/{task_id}",
        {
            "operatorSubmission": "已先查售后，复查详情页承诺和客服话术。",
            "managerReview": "通过，可沉淀为低 ROI 高退款处理案例。",
            "beforeMetrics": {"roi": "0.9", "refundRate": "8.4%"},
            "afterMetrics": {"roi": "1.4", "refundRate": "5.2%"},
        },
    )
    case_id = feedback_draft["experienceCard"]["caseId"]
    approved_case = assert_post_json(f"/api/modules/rag-memory/cases/{case_id}/approve", {"reason": "smoke test approval"})
    assert approved_case["case"]["status"] == "approved"

    assert_post_json(f"/api/modules/todo/{task_id}/assign", {"assignee_id": "U003", "reviewer_id": "U002", "operator_id": "U002", "note": "smoke test assignment"})
    assert_post_json(f"/api/modules/todo/{task_id}/accept", {"note": "smoke test accept"})
    submitted = assert_post_json(f"/api/modules/todo/{task_id}/submit", {"submitter_id": "U003", "note": "smoke test submission"})
    assert submitted["status"] == "待复核"
    approved = assert_post_json(f"/api/modules/todo/{task_id}/review", {"reviewer_id": "U002", "decision": "approve", "note": "approved"})
    assert approved["status"] == "已完成"
    assert approved["workflowStatus"] == "已归档"
    auto_draft = approved.get("feedbackDraft", {})
    assert auto_draft.get("experienceCard", {}).get("status") == "approved", "approved memory must not be downgraded by auto draft"
    assert auto_draft.get("protection") == "approved_case_preserved"

    traces = assert_status("GET", "/api/llm/traces?limit=5")
    assert "items" in traces

    print("API smoke test passed.")


if __name__ == "__main__":
    run_smoke_test()
