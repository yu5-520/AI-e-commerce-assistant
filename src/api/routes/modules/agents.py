"""V4 module Agent routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException, Query, Request

from src.services.account_service import user_id_from_headers
from src.services.creative_llm_enrichment_service import enrich_creative_agent_result
from src.services.creative_vertical_agent_service import create_creative_task, run_creative_vertical_agent
from src.services.module_agent_service import (
    create_agent_task,
    get_agent_plan,
    run_cycle_agent,
    run_module_agent,
)
from src.services.task_agent_service import generate_task_candidates, task_playbook

router = APIRouter()

AGENT_REGISTRY_VERSION = "4.5.0"


def request_user_id(request: Request) -> str:
    return user_id_from_headers(request.headers)


def current_agent_plan() -> Dict[str, Any]:
    plan = get_agent_plan()
    plan["version"] = AGENT_REGISTRY_VERSION
    plan["mode"] = "module_task_creative_feedback_action_plan_llm_gateway"
    plan["principle"] = "Agent 不放在最高控制位；模块发现问题，problemType 决定处理包，LLM 只做表达增强和草案生成。"
    existing_ids = {item.get("id") for item in plan.get("agents", [])}
    additions = [
        {"id": "llm-gateway", "name": "统一 LLM Gateway", "module": "llm", "output": "provider、prompt、guardrail、trace、fallback"},
        {"id": "tool-gateway", "name": "统一 Tool Gateway", "module": "tool", "output": "只读快照、RAG 召回、ActionPlan；不暴露真实经营动作"},
        {"id": "mcp-adapter", "name": "MCP 外部工具适配层", "module": "tool", "output": "未来接外部工具生态，不替代内部权限链路"},
        {"id": "problem-type-action-plan", "name": "问题类型处理包 Agent", "module": "task", "output": "problemType、executionPackages、证据、复核标准、失败阈值"},
        {"id": "task-generation", "name": "自动解析生成任务 Agent", "module": "task", "output": "规则命中、RAG 引用、置信度、问题类型处理包"},
        {"id": "task-playbook", "name": "任务解析运营方式 Agent", "module": "task", "output": "稳健型 / 增长型 / 利润型打法、证据要求、验收标准"},
        {"id": "creative-vertical", "name": "标题主图垂直类目 Agent", "module": "product", "output": "标题测试包、主图方向、卖点排序、LLM 表达增强、上架测试指标"},
        {"id": "feedback-flywheel", "name": "回流任务 Agent", "module": "feedback", "output": "周期摘要、学习候选、经验卡草案、反馈指标"},
    ]
    plan["agents"] = [*(plan.get("agents") or []), *[item for item in additions if item["id"] not in existing_ids]]
    plan["v45Endpoints"] = {
        "llmStatus": "/api/llm/status",
        "llmGenerate": "/api/llm/generate",
        "llmTraces": "/api/llm/traces",
        "toolGateway": "/api/llm/tools",
        "mcpBoundary": "/api/llm/mcp",
        "taskGeneration": "/api/modules/agents/tasks/generate",
        "taskPlaybook": "/api/modules/agents/tasks/{task_id}/playbook",
        "creativeVertical": "/api/modules/agents/creative/{product_id}",
        "creativeVerticalTask": "/api/modules/agents/creative/{product_id}/tasks",
        "feedbackFlywheel": "/api/modules/feedback-flywheel",
    }
    plan["v442ActionPlan"] = {
        "service": "src/services/action_plan_service.py",
        "rule": "模块负责发现问题，problemType 决定处理包，避免所有任务套同一模板。",
        "problemTypes": ["low_ctr_low_conversion", "detail_page_conversion", "low_roi_high_refund", "low_inventory_activity", "competitor_signal_to_test", "report_data_anomaly"],
        "outputs": ["actionPlan", "executionPackages", "executionSteps", "evidenceRequired", "submitMetrics", "acceptanceCriteria", "failureThreshold", "reviewFocus"],
    }
    plan["v450LlmGateway"] = {
        "service": "src/services/llm_provider_service.py",
        "guardrail": "src/services/llm_guardrail_service.py",
        "trace": "src/services/llm_trace_service.py",
        "promptTemplate": "src/services/prompt_template_service.py",
        "toolGateway": "src/services/tool_gateway_service.py",
        "mcpAdapter": "src/services/mcp_adapter_service.py",
        "rule": "LLM Provider 统一模型调用；Tool Gateway 统一安全工具；MCP 只做未来外部工具适配。",
    }
    plan["registryBoundary"] = "Agent 注册表只描述能力和入口；所有经营动作仍走统一任务池、账号权限和人工复核。"
    return plan


@router.get("/agents")
def agents() -> Dict[str, Any]:
    return current_agent_plan()


@router.post("/agents/tasks/generate")
def task_generation_agent(request: Request, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    source_module = body.get("sourceModule") or body.get("source_module") or body.get("module") or "product"
    result = generate_task_candidates(
        source_module=source_module,
        entity_id=body.get("entityId") or body.get("entity_id"),
        body=body,
        user_id=request_user_id(request),
    )
    if not result.get("candidates"):
        raise HTTPException(status_code=404, detail=result.get("message") or "task candidate not found")
    return result


@router.get("/agents/tasks/{task_id}/playbook")
def task_playbook_agent(
    request: Request,
    task_id: str,
    preferred_style: str | None = Query(default=None),
) -> Dict[str, Any]:
    result = task_playbook(task_id, user_id=request_user_id(request), preferred_style=preferred_style)
    if not result:
        raise HTTPException(status_code=404, detail="task playbook not found")
    return result


@router.post("/agents/creative/{product_id}")
def creative_vertical_agent(request: Request, product_id: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    result = run_creative_vertical_agent(product_id, body=body or {}, user_id=request_user_id(request))
    if not result:
        raise HTTPException(status_code=404, detail="creative vertical agent product not found")
    return enrich_creative_agent_result(result)


@router.get("/agents/creative/{product_id}")
def creative_vertical_agent_get(
    request: Request,
    product_id: str,
    task_goal: str | None = Query(default=None),
    platform: str | None = Query(default=None),
    category_id: str | None = Query(default=None),
) -> Dict[str, Any]:
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
    return run_cycle_agent(target=target, user_id=request_user_id(request))


@router.get("/agents/{module}/{entity_id}")
def module_agent(
    request: Request,
    module: str,
    entity_id: str,
    mode: str = Query(default="analysis"),
) -> Dict[str, Any]:
    result = run_module_agent(module, entity_id, mode=mode, user_id=request_user_id(request))
    if not result:
        raise HTTPException(status_code=404, detail="module agent result not found")
    return result


@router.post("/agents/{module}/{entity_id}/tasks")
def module_agent_task(
    request: Request,
    module: str,
    entity_id: str,
    body: Dict[str, Any] | None = Body(default=None),
) -> Dict[str, Any]:
    body = body or {}
    result = create_agent_task(
        module,
        entity_id,
        draft_index=int(body.get("draftIndex", body.get("draft_index", 0)) or 0),
        mode=body.get("mode") or "analysis",
        user_id=request_user_id(request),
    )
    if not result:
        raise HTTPException(status_code=400, detail="cannot create task from module agent draft")
    return result
