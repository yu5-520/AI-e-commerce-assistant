"""Internal Tool Gateway for V4.5.

This is not MCP yet. It is the stable internal interface that Agents and LLM
prompts can depend on. MCP can later be added as one adapter behind this gateway.
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.services.action_plan_service import action_plan_for_problem, infer_action_problem_type
from src.services.experience_memory_service import search_cases
from src.services.module_data_service import COMPETITORS, LISTINGS, PRODUCTS, TRAFFIC, find_by_id
from src.services.module_task_service import find_task

TOOL_GATEWAY_VERSION = "4.5.0"

SAFE_TOOLS = {
    "get_product_snapshot",
    "get_traffic_snapshot",
    "get_competitor_snapshot",
    "get_listing_snapshot",
    "get_task_snapshot",
    "search_rag_memory",
    "build_action_plan",
}

BLOCKED_TOOLS = {
    "change_price",
    "publish_product",
    "increase_ad_budget",
    "refund_order",
    "write_erp",
    "write_crm",
}


def list_tools() -> Dict[str, Any]:
    return {
        "version": TOOL_GATEWAY_VERSION,
        "safeTools": sorted(SAFE_TOOLS),
        "blockedTools": sorted(BLOCKED_TOOLS),
        "rule": "工具网关只暴露只读快照、RAG 召回和草案生成；真实经营动作不开放给 LLM。",
    }


def _snapshot(module: str, entity_id: str) -> Dict[str, Any] | None:
    source = {
        "product": PRODUCTS,
        "traffic": TRAFFIC,
        "competitor": COMPETITORS,
        "listing": LISTINGS,
    }.get(module)
    if source is None:
        return None
    return find_by_id(source, entity_id)


def call_tool(name: str, args: Dict[str, Any] | None = None) -> Dict[str, Any]:
    args = args or {}
    if name in BLOCKED_TOOLS:
        return {"version": TOOL_GATEWAY_VERSION, "ok": False, "blocked": True, "tool": name, "message": "该工具属于真实经营动作，不能暴露给 LLM。"}
    if name not in SAFE_TOOLS:
        return {"version": TOOL_GATEWAY_VERSION, "ok": False, "blocked": True, "tool": name, "message": "未知或未授权工具。"}
    if name == "get_product_snapshot":
        data = _snapshot("product", args.get("productId") or args.get("entityId") or "")
    elif name == "get_traffic_snapshot":
        data = _snapshot("traffic", args.get("trafficId") or args.get("entityId") or "")
    elif name == "get_competitor_snapshot":
        data = _snapshot("competitor", args.get("competitorId") or args.get("entityId") or "")
    elif name == "get_listing_snapshot":
        data = _snapshot("listing", args.get("listingId") or args.get("entityId") or "")
    elif name == "get_task_snapshot":
        data = find_task(args.get("taskId") or args.get("entityId") or "")
    elif name == "search_rag_memory":
        data = search_cases(
            query=args.get("query"),
            category_id=args.get("categoryId"),
            platform=args.get("platform"),
            store_id=args.get("storeId"),
            problem_type=args.get("problemType"),
            effective_only=bool(args.get("effectiveOnly", False)),
            limit=int(args.get("limit", 5) or 5),
        )
    elif name == "build_action_plan":
        item = args.get("item") or {}
        problem_type = args.get("problemType") or infer_action_problem_type(item, source_module=args.get("sourceModule"))
        data = action_plan_for_problem(problem_type, item=item, source_module=args.get("sourceModule"), rag_items=args.get("ragItems") or [])
    else:
        data = None
    return {"version": TOOL_GATEWAY_VERSION, "ok": data is not None, "tool": name, "data": data}


def tool_gateway_summary() -> Dict[str, Any]:
    return {
        **list_tools(),
        "mcpPosition": "MCP 以后只作为外部工具适配层，不能替代内部权限、任务池、ActionPlan 和审计链路。",
    }
