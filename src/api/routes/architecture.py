"""Architecture visibility routes for SaaS governance."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends

from src.core.context import UserContext, get_current_context
from src.services.p0_architecture_service import p0_architecture_summary
from src.services.v7_saas_control_plane_service import v7_saas_architecture_summary

router = APIRouter(prefix="/api/architecture", tags=["architecture"])


@router.get("/p0")
async def p0_architecture(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Return the P0 SaaS architecture decomposition and current scope plan."""

    return p0_architecture_summary(ctx)


@router.get("/v7")
async def v7_saas_architecture(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Return the V7 SaaS control-plane architecture and workflow governance baseline."""

    return v7_saas_architecture_summary(ctx)


@router.get("/context")
async def current_context(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Expose current demo UserContext for permission-scope verification."""

    return {"context": ctx.to_dict(), "auditMeta": ctx.audit_meta()}
