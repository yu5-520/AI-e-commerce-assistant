"""V4 module Agent routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException, Query, Request

from src.services.account_service import user_id_from_headers
from src.services.module_agent_service import (
    create_agent_task,
    get_agent_plan,
    run_cycle_agent,
    run_module_agent,
)

router = APIRouter()


def request_user_id(request: Request) -> str:
    return user_id_from_headers(request.headers)


@router.get("/agents")
def agents() -> Dict[str, Any]:
    return get_agent_plan()


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
