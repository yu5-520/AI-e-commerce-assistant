"""Architecture visibility routes for SaaS governance."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from src.core.context import UserContext, get_current_context
from src.services.p0_architecture_service import p0_architecture_summary
from src.services.v7_saas_control_plane_service import v7_saas_architecture_summary
from src.services.v72_tenant_config_console_service import set_feature_flag_status, tenant_config_console_summary, upsert_rollout_rule
from src.services.v73_config_audit_service import compare_config_audit, config_audit_summary, rollback_config_audit

router = APIRouter(prefix="/api/architecture", tags=["architecture"])


@router.get("/p0")
async def p0_architecture(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Return the P0 SaaS architecture decomposition and current scope plan."""
    return p0_architecture_summary(ctx)


@router.get("/v7")
async def v7_saas_architecture(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Return the V7.3 SaaS control-plane architecture and workflow governance baseline."""
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


@router.get("/v7/config-audits")
async def v73_config_audits(
    action: str | None = Query(default=None),
    target_key: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    ctx: UserContext = Depends(get_current_context),
) -> Dict[str, Any]:
    """Search V7.3 tenant configuration audit events."""
    return config_audit_summary(ctx, action=action, target_key=target_key, limit=limit)


@router.get("/v7/config-audits/{audit_id}/compare")
async def v73_compare_config_audit(audit_id: str, ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Compare a config audit event with previous state."""
    try:
        return compare_config_audit(audit_id, ctx)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/v7/config-audits/{audit_id}/rollback")
async def v73_rollback_config_audit(audit_id: str, ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Rollback a config audit event to previous state and write a rollback audit."""
    try:
        return rollback_config_audit(audit_id, ctx)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/context")
async def current_context(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Expose current demo UserContext for permission-scope verification."""
    return {"context": ctx.to_dict(), "auditMeta": ctx.audit_meta()}
