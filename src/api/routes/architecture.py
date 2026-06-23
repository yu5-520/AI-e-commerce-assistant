"""Architecture visibility routes for SaaS governance."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, HTTPException

from src.core.context import UserContext, get_current_context
from src.services.p0_architecture_service import p0_architecture_summary
from src.services.v7_saas_control_plane_service import v7_saas_architecture_summary
from src.services.v72_tenant_config_console_service import set_feature_flag_status, tenant_config_console_summary, upsert_rollout_rule

router = APIRouter(prefix="/api/architecture", tags=["architecture"])


@router.get("/p0")
async def p0_architecture(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Return the P0 SaaS architecture decomposition and current scope plan."""
    return p0_architecture_summary(ctx)


@router.get("/v7")
async def v7_saas_architecture(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Return the V7.2 SaaS control-plane architecture and workflow governance baseline."""
    return v7_saas_architecture_summary(ctx)


@router.get("/v7/tenant-config")
async def v72_tenant_config(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Return tenant configuration, feature flags, rollout evaluation, and console permissions."""
    return tenant_config_console_summary(ctx)


@router.post("/v7/feature-flags/{flag_key}")
async def v72_upsert_feature_flag(flag_key: str, body: Dict[str, Any] | None = Body(default=None), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Create or update a V7.2 feature flag from the console."""
    try:
        return set_feature_flag_status(flag_key, body or {}, ctx)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/v7/feature-flags/{flag_key}/rollout")
async def v72_upsert_rollout_rule(flag_key: str, body: Dict[str, Any] | None = Body(default=None), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Create or update a V7.2 rollout rule from the console."""
    try:
        return upsert_rollout_rule(flag_key, body or {}, ctx)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/context")
async def current_context(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Expose current demo UserContext for permission-scope verification."""
    return {"context": ctx.to_dict(), "auditMeta": ctx.audit_meta()}
