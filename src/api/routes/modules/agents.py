"""V5 module Agent routes."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException, Query, Request

from src.services.account_service import user_id_from_headers
from src.services.agent_llm_enrichment_service import enrich_module_agent_result, enrich_task_generation_result, enrich_task_playbook_result
from src.services.creative_llm_enrichment_service import enrich_creative_agent_result
from src.services.creative_vertical_agent_service import create_creative_task, run_creative_vertical_agent
from src.services.module_agent_service import get_agent_plan, run_cycle_agent, run_module_agent
from src.services.module_task_service import create_task
from src.services.task_agent_service import generate_task_candidates, task_playbook

router = APIRouter()
AGENT_REGISTRY_VERSION = "5.0.5"


def request_user_id(request: Request) -> str:
    return user_id_from_headers(request.headers)


def current_agent_plan() -> Dict[str, Any]:
    plan = get_agent_plan()
    plan["version"] = AGENT_REGISTRY_VERSION
    plan["mode"] = "decision_task_draft_agent_layer"
    plan["principle"] = "导入数据生成只读证据和 Agent 判断；运营只补系统不知道的现实变量，并选择主经营路径。"
    plan["decisionTaskDraft"] = {
        "service": "src/services/action_plan_service.py",
        "outputs": ["readonlyEvidence", "commonActions", "supplementSchema", "decisionPaths", "selectedPathId", "operatorSupplement", "reviewPlan"],
        "uiRule": "前端默认展示任务草案和路径选择，不展示问题处理包、方案补充、人工确认等工程模块。",
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
        item["task"] = f"选择“{selected_path.get('pathName')}”路径，补充现实变量后进入任务池，等待下一轮数据复盘。"
    item["operatorSupplement"] = supplement
    item["reviewPlan"] = body.get("reviewPlan") or body.get("review_plan") or plan.get("reviewPlan") or {}
    item["taskType"] = "V5 经营路径任务"
    item["taskSignal"] = "readonlyEvidence + supplement + selectedDecisionPath + reviewPlan"
    item["agentJudgment"] = {**(item.get("agentJudgment") or {}), "status": "decision_confirmed", "selectedPathId": selected_path_id, "operatorSupplementKeys": list(supplement.keys()), "boundary": "运营选择路径并补充现实变量；系统等待下一轮数据复盘。"}
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
def creative_vertical_task(request: Request, product_id: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    result = create_creative_task(product_id, body=body or {}, user_id=request_user_id(request))
    if not result:
        raise HTTPException(status_code=400, detail="cannot create task from creative vertical agent")
    result["agent"] = enrich_creative_agent_result(result.get("agent") or {})
    return result


@router.get("/agents/cycle/{target}")
def cycle_agent(request: Request, target: str = "日报") -> Dict[str, Any]:
    return enrich_module_agent_result(run_cycle_agent(target=target, user_id=request_user_id(request)))


@router.get("/agents/{module}/{entity_id}")
def module_agent(request: Request, module: str, entity_id: str, mode: str = Query(default="analysis")) -> Dict[str, Any]:
    result = run_module_agent(module, entity_id, mode=mode, user_id=request_user_id(request))
    if not result:
        raise HTTPException(status_code=404, detail="module agent result not found")
    return enrich_module_agent_result(result)


@router.post("/agents/{module}/{entity_id}/tasks")
def module_agent_task(request: Request, module: str, entity_id: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    agent_result = run_module_agent(module, entity_id, mode=body.get("mode") or "analysis", user_id=request_user_id(request))
    if not agent_result:
        raise HTTPException(status_code=400, detail="cannot create task from module agent draft")
    drafts = agent_result.get("taskDrafts") or []
    draft_index = int(body.get("draftIndex", body.get("draft_index", 0)) or 0)
    if draft_index < 0 or draft_index >= len(drafts):
        raise HTTPException(status_code=400, detail="task draft not found")
    draft = _merge_decision_payload(drafts[draft_index], body)
    task = create_task(draft)
    return {"agent": enrich_module_agent_result(agent_result), "task": task, "message": "经营路径任务已进入统一任务池。"}
