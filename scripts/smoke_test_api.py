"""API smoke test for the current AI ERP operating advisor V4.4.2 product surface.

Run from repository root:
    python scripts/smoke_test_api.py

This smoke test checks the current `/api/modules/*` product trunk: Agent registry,
problem-type Action Plans, RAG memory, creative test packages, feedback flywheel,
and task lifecycle with approved-memory protection.
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
    assert_keys(health, ["ok", "version", "product", "mode", "safety", "account_entry"], "health")
    assert health["ok"] is True
    assert health["version"] == app.version
    assert health["api_entry"] == "/api/modules/*"
    assert health["v442_problem_type_action_plan"] is True
    assert health["v440_feedback_flywheel"] is True
    assert health["feedback_requires_human_approval"] is True

    db_status = assert_status("GET", "/api/system/db-status")
    assert "task_status" in {item["table_name"] for item in db_status["tables"]}

    accounts = assert_status("GET", "/api/accounts")
    assert_keys(accounts, ["currentUser", "roles", "permissions", "users", "stores", "taskFlow"], "accounts")

    for path in [
        "/api/modules/dashboard",
        "/api/modules/operating-unit",
        "/api/modules/product",
        "/api/modules/competitor",
        "/api/modules/listing",
        "/api/modules/traffic",
        "/api/modules/report",
        "/api/modules/log",
    ]:
        payload = assert_status("GET", path)
        assert payload is not None, f"{path} should return payload"

    agents = assert_status("GET", "/api/modules/agents")
    assert_keys(agents, ["version", "agents", "boundary", "forbiddenActions", "v44Endpoints", "v442ActionPlan"], "module agents")
    assert agents["version"] == app.version, "Agent registry should align with FastAPI version"
    agent_ids = {item.get("id") for item in agents["agents"]}
    assert {"problem-type-action-plan", "task-generation", "task-playbook", "creative-vertical", "feedback-flywheel"}.issubset(agent_ids)

    product_agent = assert_status("GET", "/api/modules/agents/product/P002")
    assert_keys(product_agent, ["agentId", "summary", "evidence", "suggestions", "taskDrafts", "forbiddenActions", "actionPlan", "executionPackages"], "product agent")
    assert_action_plan(product_agent["taskDrafts"][0], "product task draft")
    assert "不直接改价" in product_agent["forbiddenActions"]

    generated = assert_post_json("/api/modules/agents/tasks/generate", {"sourceModule": "traffic", "entityId": "T001", "autoCreate": False})
    assert generated["candidates"]
    candidate = generated["candidates"][0]
    assert candidate["taskDraft"]["taskType"] == "V4.4.2 问题类型处理包"
    assert candidate["actionPlanType"], "candidate should expose actionPlanType"
    assert candidate["executionPackages"], "candidate should expose targeted execution packages"
    assert_action_plan(candidate["taskDraft"], "generated task draft")

    playbook_seed = assert_status("GET", "/api/modules/rag-memory/search?problem_type=low_roi_high_refund&category_id=home_living_goods")
    assert playbook_seed["items"], "RAG memory should retrieve seeded playbook"

    creative = assert_post_json(
        "/api/modules/agents/creative/P002",
        {"taskGoal": "提升点击率并降低安装预期退款", "platform": "拼多多", "categoryId": "home_living_goods"},
    )
    assert creative["agentName"] == "标题主图垂直类目 Agent"
    assert len(creative["titleVariants"]) >= 3
    assert len(creative["mainImageDirections"]) >= 3
    assert len(creative["testPackages"]) >= 3, "creative Agent should generate ready-to-test packages"
    first_package = creative["testPackages"][0]
    assert_keys(first_package, ["title", "mainImageDirection", "firstImageText", "operatorAction", "submitMetrics", "fitTraffic"], "creative test package")
    assert creative["taskDraft"]["taskType"] == "V4.3 垂直类目创意测试"
    assert creative["taskDraft"]["executionSteps"], "creative task draft should carry operator execution steps"

    creative_task = assert_post_json(
        "/api/modules/agents/creative/P002/tasks",
        {"packageIndex": 1, "taskGoal": "测试标题主图点击率", "platform": "拼多多", "categoryId": "home_living_goods"},
    )
    assert creative_task["task"]["selectedPackage"]["packageName"].startswith("方案 B"), "packageIndex should select a concrete test package"
    assert creative_task["task"]["executionSteps"], "created creative task should be executable by operator"

    feedback = assert_status("GET", "/api/modules/feedback-flywheel")
    assert_keys(feedback, ["agentName", "chain", "memorySummary", "agentEvalMetrics", "learningCandidates", "forbiddenActions"], "feedback flywheel")
    assert feedback["agentName"] == "回流任务 Agent"
    assert "不自动批准经验入库" in feedback["forbiddenActions"]

    cycle_feedback = assert_status("GET", "/api/modules/feedback-flywheel/cycle/日报")
    assert_keys(cycle_feedback, ["agentName", "summary", "draftSections", "learningCandidates", "forbiddenActions"], "cycle feedback")

    todo_reset = assert_status("POST", "/api/modules/todo/reset")
    assert_keys(todo_reset, ["tasks", "logs"], "todo reset")

    todo = assert_status("GET", "/api/modules/todo")
    assert todo["activeTasks"], "todo should expose active task pool"
    task_id = todo["activeTasks"][0]["id"]

    task_agent = assert_status("GET", f"/api/modules/agents/task/{task_id}?mode=breakdown")
    assert_keys(task_agent, ["actionPlan", "executionPackages", "taskDrafts", "suggestions"], "module task agent")
    assert_action_plan(task_agent["taskDrafts"][0], "task agent draft")

    task_playbook = assert_status("GET", f"/api/modules/agents/tasks/{task_id}/playbook")
    assert_keys(task_playbook, ["actionPlan", "executionPackages", "strategies"], "task playbook")
    assert len(task_playbook["strategies"]) >= 3
    assert task_playbook["executionPackages"], "task playbook should expose execution packages"

    feedback_draft = assert_post_json(
        f"/api/modules/rag-memory/feedback/tasks/{task_id}",
        {
            "operatorSubmission": "已先查售后，复查详情页承诺和客服话术。",
            "managerReview": "通过，可沉淀为低 ROI 高退款处理案例。",
            "beforeMetrics": {"roi": "0.9", "refundRate": "8.4%"},
            "afterMetrics": {"roi": "1.4", "refundRate": "5.2%"},
        },
    )
    assert feedback_draft["experienceCard"]["sourceTaskId"] == task_id
    assert feedback_draft["needsHumanReviewBeforeWrite"] is True
    case_id = feedback_draft["experienceCard"]["caseId"]
    approved_case = assert_post_json(f"/api/modules/rag-memory/cases/{case_id}/approve", {"reason": "smoke test approval"})
    assert approved_case["case"]["status"] == "approved"

    assert_post_json(
        f"/api/modules/todo/{task_id}/assign",
        {"assignee_id": "U003", "reviewer_id": "U002", "operator_id": "U002", "note": "smoke test assignment"},
    )
    assert_post_json(f"/api/modules/todo/{task_id}/accept", {"note": "smoke test accept"})
    submitted = assert_post_json(f"/api/modules/todo/{task_id}/submit", {"submitter_id": "U003", "note": "smoke test submission"})
    assert submitted["status"] == "待复核"

    approved = assert_post_json(
        f"/api/modules/todo/{task_id}/review",
        {"reviewer_id": "U002", "decision": "approve", "note": "approved"},
    )
    assert approved["status"] == "已完成"
    assert approved["workflowStatus"] == "已归档"
    auto_draft = approved.get("feedbackDraft", {})
    assert auto_draft.get("needsHumanReviewBeforeWrite") is True
    assert auto_draft.get("experienceCard", {}).get("status") == "approved", "approved memory must not be downgraded by auto draft"
    assert auto_draft.get("protection") == "approved_case_preserved"

    cycle_draft = assert_post_json("/api/modules/feedback-flywheel/cycle/日报/draft", {"limit": 3})
    assert_keys(cycle_draft, ["agentName", "draftedCount", "drafts", "needsHumanReviewBeforeWrite", "writeBoundary"], "cycle memory draft")
    assert cycle_draft["needsHumanReviewBeforeWrite"] is True

    active_after_review = assert_status("GET", "/api/modules/todo")
    assert task_id not in {task["id"] for task in active_after_review["activeTasks"]}

    print("API smoke test passed.")


if __name__ == "__main__":
    run_smoke_test()
