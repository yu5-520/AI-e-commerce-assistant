"""V9 module Agent routes."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request

from src.core.context import UserContext, get_current_context
from src.services.account_service import user_id_from_headers
from src.services.agent_llm_enrichment_service import enrich_module_agent_result, enrich_task_generation_result, enrich_task_playbook_result
from src.services.creative_llm_enrichment_service import enrich_creative_agent_result
from src.services.creative_task_repository_sync_service import create_creative_task_with_repository
from src.services.creative_vertical_agent_service import run_creative_vertical_agent
from src.services.module_agent_service import get_agent_plan, run_cycle_agent, run_module_agent
from src.services.task_agent_service import generate_task_candidates, task_playbook
from src.services.task_repository_write_service import create_task_with_repository

router = APIRouter()
AGENT_REGISTRY_VERSION = "9.3.0"


def request_user_id(request: Request) -> str:
    return user_id_from_headers(request.headers)


def current_agent_plan() -> Dict[str, Any]:
    plan = get_agent_plan()
    plan["version"] = AGENT_REGISTRY_VERSION
    plan["mode"] = "v930_frontend_module_consistency"
    plan["principle"] = "Agent 输出仍在原模块和任务详情中呈现；V8 权重、RAG、审批和复盘信息作为后端证据链补强，不新增前端主模块。"
    plan["v93FrontendModules"] = {
        "service": "src/services/v93_frontend_module_contract_service.py",
        "architectureEndpoint": "/api/architecture/v9/frontend-modules",
        "stableModules": ["dashboard", "operating-unit", "product", "competitor", "listing", "traffic", "report", "todo", "log", "system-status", "accounts"],
        "rule": "前端主模块保持稳定，后端能力通过套餐展示深度补强原模块。",
    }
    plan["v92BackendFlow"] = {
        "service": "src/services/v92_backend_flow_service.py",
        "architectureEndpoint": "/api/architecture/v9/backend-flow",
        "flow": ["ImportJob", "DataVersion", "RawRows", "ModuleProjection", "AlertEvent", "WeightSignal", "DecisionTask", "AgentReport", "ApprovalFlow", "ExecutionFeedback", "ReviewLog", "RagMemoryCandidate"],
        "rule": "Agent 任务生成读取模块数据、权重上下文、RAG 证据和 ActionPlan；不按模块套同一模板。",
    }
    plan["decisionTaskDraft"] = {
        "service": "src/services/action_plan_service.py",
        "outputs": ["readonlyEvidence", "supplementSchema", "decisionPaths", "selectedPathId", "operatorSupplement", "reviewPlan"],
        "uiRule": "前端展示路径小标签和行动顺序；选择路径后直接进入处理中。",
    }
    plan["taskRepositoryWritePath"] = {
        "version": AGENT_REGISTRY_VERSION,
        "service": "src/services/task_repository_write_service.py",
        "rule": "Agent 入池任务通过 TaskRepository 写路径持久化，保留旧 Demo 返回结构。创意 Agent 入池也同步到 TaskRepository。",
    }
    return plan


def _merge_decision_payload(draft: Dict[str, Any], body: Dict[str, Any]) -> Dict[str, Any]:
    item = deepcopy(draft)
    plan = item.get("actionPlan") or {}
    selected_path_id = body.get("selectedPathId") or body.get("selected_path_id") or plan.get("recommendedPathId")
    selected_path = next((path for path in plan.get("decisionPaths") or [] if path.get("pathId") == selected_path_id), None)
    supplement = body.get("operatorSupplement") or body.get("operator_supplement") or {}
    item["selectedPathId"] = selected_path_id
    if selected_path:
        item["selectedDecisionPath"] = selected_path
        item["actionType"] = selected_path.get("pathName") or item.get("actionType")
        item["task"] = f"执行“{selected_path.get('pathName')}”路径，并提交截图、处理结果和复盘指标。"
        item["reason"] = f"已在详情页选择“{selected_path.get('pathName')}”路径，待办页只补充执行证据和成果。"
    item["operatorSupplement"] = supplement
    item["reviewPlan"] = body.get("reviewPlan") or body.get("review_plan") or plan.get("reviewPlan") or {}
    item["taskType"] = "V5 经营路径执行"
    item["taskSignal"] = "selectedDecisionPath + executionEvidence + reviewPlan"
    item["status"] = "处理中"
    item["workflowStatus"] = "处理中"
    item["autoAccepted"] = True
    item["acceptedFrom"] = "decision_draft_confirmed"
    item["taskLayer"] = item.get("taskLayer") or "operator_execution"
    item["agentJudgment"] = {**(item.get("agentJudgment") or {}), "status": "decision_path_auto_accepted", "selectedPathId": selected_path_id, "operatorSupplementKeys": list(supplement.keys()), "boundary": "已选路径直接进入处理中；待办只提交执行证据和等待复盘。"}
    return item


@router.get("/agents")
def agents() -> Dict[str, Any]:
    return current_agent_plan()


@router.post("/agents/tasks/generate")
def task_generation_agent(request: Request, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    source_module = body.get("sourceModule") or body.get("source_module") or body.get("module") or "product"
    result = generate_task_candidates(source_module=source_module, entity_id=body.get("entityId") or body.get("entity_id"), body=body, user_id=request_user_id(request))
    if not result.get("candidates"):
        raise HTTPException(status_code=404, detail=result.get("message") or "task candidate not found")
    return enrich_task_generation_result(result)


@router.get("/agents/tasks/{task_id}/playbook")
def task_playbook_agent(request: Request, task_id: str, preferred_style: str | None = Query(default=None)) -> Dict[str, Any]:
    result = task_playbook(task_id, user_id=request_user_id(request), preferred_style=preferred_style)
    if not result:
        raise HTTPException(status_code=404, detail="task playbook not found")
    return enrich_task_playbook_result(result)


@router.post("/agents/creative/{product_id}")
def creative_vertical_agent(request: Request, product_id: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    result = run_creative_vertical_agent(product_id, body=body or {}, user_id=request_user_id(request))
    if not result:
        raise HTTPException(status_code=404, detail="creative vertical agent product not found")
    return enrich_creative_agent_result(result)


@router.get("/agents/creative/{product_id}")
def creative_vertical_agent_get(request: Request, product_id: str, task_goal: str | None = Query(default=None), platform: str | None = Query(default=None), category_id: str | None = Query(default=None)) -> Dict[str, Any]:
    body: Dict[str, Any] = {}
    if task_goal:
        body["taskGoal"] = task_goal
    if platform:
        body["platform"] = platform
    if category_id:
        body["categoryId"] = category_id
    result = run_creative_vertical_agent(product_id, body=body, user_id=request_user_id(request))
    if not result:
        raise HTTPException(status_code=404, detail="creative vertical agent product not found")
    return enrich_creative_agent_result(result)


@router.post("/agents/creative/{product_id}/tasks")
def creative_vertical_task(
    request: Request,
    product_id: str,
    body: Dict[str, Any] | None = Body(default=None),
    ctx: UserContext = Depends(get_current_context),
) -> Dict[str, Any]:
    result = create_creative_task_with_repository(product_id, body=body or {}, ctx=ctx)
    if not result:
        raise HTTPException(status_code=400, detail="cannot create task from creative vertical agent")
    result["agent"] = enrich_creative_agent_result(result.get("agent") or {})
    result["message"] = "创意测试任务已进入统一任务池，并已同步到 TaskRepository。"
    return result


@router.get("/agents/cycle/{target}")
def cycle_agent(request: Request, target: str = "日报") -> Dict[str, Any]:
    return enrich_module_agent_result(run_cycle_agent(target=target, user_id=request_user_id(request)))


@router.get("/agents/{module}/{entity_id}")
def module_agent(request: Request, module: str, entity_id: str, mode: str = Query(default="analysis")) -> Dict[str, Any]:
    result = run_module_agent(module, entity_id, mode=mode, user_id=request_user_id(request))
    if not result:
        raise HTTPException(status_code=404, detail="agent entity not found")
    return enrich_module_agent_result(result)


@router.post("/agents/{module}/{entity_id}/tasks")
def module_agent_task(request: Request, module: str, entity_id: str, body: Dict[str, Any] | None = Body(default=None), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    result = run_module_agent(module, entity_id, mode="task", user_id=request_user_id(request))
    if not result:
        raise HTTPException(status_code=404, detail="agent entity not found")
    draft = (result.get("taskDrafts") or [{}])[0]
    task = _merge_decision_payload(draft, body or {})
    created = create_task_with_repository(task, ctx=ctx)
    created["agent"] = enrich_module_agent_result(result)
    created["message"] = "Agent 任务已进入统一任务池，并已同步到 TaskRepository。"
    return created
