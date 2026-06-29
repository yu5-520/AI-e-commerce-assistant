"""V14.1 module Agent routes."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException, Query, Request

from src.services.account_service import user_id_from_headers
from src.services.agent_llm_enrichment_service import enrich_module_agent_result, enrich_task_generation_result, enrich_task_playbook_result
from src.services.creative_llm_enrichment_service import enrich_creative_agent_result
from src.services.creative_vertical_agent_service import run_creative_vertical_agent
from src.services.module_agent_service import get_agent_plan, run_cycle_agent, run_module_agent
from src.services.task_agent_service import generate_task_candidates, task_playbook

router = APIRouter()
AGENT_REGISTRY_VERSION = "14.1.0"


def request_user_id(request: Request) -> str:
    return user_id_from_headers(request.headers)


def current_agent_plan() -> Dict[str, Any]:
    plan = get_agent_plan()
    plan["version"] = AGENT_REGISTRY_VERSION
    plan["mode"] = "v14_1_candidate_only_for_legacy_module_agents"
    plan["principle"] = "模块Agent可返回分析和候选，但不再绕过 task_snapshot_station 直接写入可见任务池。"
    plan["taskMainline"] = "signal_pool -> rag_context -> agent_judgment -> task_snapshot -> task_pool"
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
        item["reason"] = f"已在详情页选择“{selected_path.get('pathName')}”路径。"
    item["operatorSupplement"] = supplement
    item["reviewPlan"] = body.get("reviewPlan") or body.get("review_plan") or plan.get("reviewPlan") or {}
    item["status"] = "candidate_only"
    item["workflowStatus"] = "candidate_only"
    item["agentJudgment"] = {**(item.get("agentJudgment") or {}), "status": "candidate_only_v14_1", "selectedPathId": selected_path_id, "operatorSupplementKeys": list(supplement.keys())}
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
    enriched = enrich_task_generation_result(result)
    enriched["mode"] = "candidate_only_v14_1"
    enriched["rule"] = "V14.1：候选生成不直接写入任务池；入池必须经过 task_snapshot_station。"
    return enriched


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
    result = run_creative_vertical_agent(product_id, body=body or {}, user_id=request_user_id(request))
    if not result:
        raise HTTPException(status_code=404, detail="creative vertical agent product not found")
    return {"version": AGENT_REGISTRY_VERSION, "mode": "candidate_only_v14_1", "agent": enrich_creative_agent_result(result), "createdTaskCount": 0, "rule": "V14.1：创意Agent不再直接写入任务池。"}


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
def module_agent_task(request: Request, module: str, entity_id: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    result = run_module_agent(module, entity_id, mode="task", user_id=request_user_id(request))
    if not result:
        raise HTTPException(status_code=404, detail="agent entity not found")
    draft = (result.get("taskDrafts") or [{}])[0]
    candidate = _merge_decision_payload(draft, body or {})
    return {"version": AGENT_REGISTRY_VERSION, "mode": "candidate_only_v14_1", "candidate": candidate, "agent": enrich_module_agent_result(result), "createdTaskCount": 0, "rule": "V14.1：模块Agent任务按钮只返回候选，不再直接写入任务池。"}
