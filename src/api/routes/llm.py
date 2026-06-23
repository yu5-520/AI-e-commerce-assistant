"""LLM Gateway routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, Query

from src.core.context import UserContext, get_current_context
from src.services.llm_gateway_service import gateway_generate_json, llm_gateway_control_summary
from src.services.llm_guardrail_service import guardrail_summary
from src.services.llm_provider_service import llm_status
from src.services.llm_trace_service import list_llm_traces, llm_trace_summary
from src.services.mcp_adapter_service import list_mcp_servers, mcp_adapter_summary
from src.services.prompt_template_service import prompt_summary
from src.services.tool_gateway_service import call_tool, tool_gateway_summary

router = APIRouter(prefix="/api/llm", tags=["llm"])


@router.get("/status")
def status(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return {
        "llm": llm_status(),
        "gatewayControl": llm_gateway_control_summary(ctx),
        "guardrail": guardrail_summary(),
        "prompts": prompt_summary(),
        "toolGateway": tool_gateway_summary(),
        "mcpAdapter": mcp_adapter_summary(),
        "trace": llm_trace_summary(),
    }


@router.post("/generate")
def generate(body: Dict[str, Any] | None = Body(default=None), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    body = body or {}
    return gateway_generate_json(
        ctx,
        prompt_name=body.get("promptName") or "module_report_summary",
        payload=body.get("payload") or {},
        expected_keys=body.get("expectedKeys") or [],
        agent_name=body.get("agentName") or "Manual LLM Test",
        schema_name=body.get("schemaName") or "manual_json",
        use_cache=body.get("useCache", True) is not False,
    )


@router.get("/gateway")
def gateway(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return llm_gateway_control_summary(ctx)


@router.get("/traces")
def traces(limit: int = Query(default=50), agent_name: str | None = Query(default=None)) -> Dict[str, Any]:
    return {"items": list_llm_traces(limit=limit, agent_name=agent_name), "summary": llm_trace_summary()}


@router.get("/tools")
def tools() -> Dict[str, Any]:
    return tool_gateway_summary()


@router.post("/tools/{tool_name}")
def tool_call(tool_name: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    return call_tool(tool_name, body or {})


@router.get("/mcp")
def mcp() -> Dict[str, Any]:
    return {"adapter": mcp_adapter_summary(), "servers": list_mcp_servers()}
