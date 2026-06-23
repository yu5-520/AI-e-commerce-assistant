"""Architecture visibility routes for SaaS governance and V8 weight system."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from src.core.context import UserContext, get_current_context
from src.services.p0_architecture_service import p0_architecture_summary
from src.services.v7_saas_control_plane_service import v7_saas_architecture_summary
from src.services.v72_tenant_config_console_service import set_feature_flag_status, tenant_config_console_summary, upsert_rollout_rule
from src.services.v73_config_audit_service import compare_config_audit, config_audit_summary, rollback_config_audit
from src.services.v74_release_governance_service import release_governance_summary
from src.services.v75_release_alert_service import generate_release_alerts, release_alert_summary
from src.services.v80_weight_snapshot_service import generate_weight_snapshots, weight_snapshot_summary
from src.services.v81_weight_comparison_service import generate_weight_comparisons, weight_comparison_summary
from src.services.v82_weight_rag_gate_service import generate_weight_rag_hits, weight_rag_summary
from src.services.v83_linked_metric_relation_service import generate_linked_metric_relations, linked_relation_summary
from src.services.v84_weight_score_service import generate_weight_scores, weight_score_summary

router = APIRouter(prefix="/api/architecture", tags=["architecture"])


@router.get("/p0")
async def p0_architecture(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return p0_architecture_summary(ctx)


@router.get("/v7")
async def v7_saas_architecture(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return v7_saas_architecture_summary(ctx)


@router.get("/v7/tenant-config")
async def v72_tenant_config(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return tenant_config_console_summary(ctx)


@router.post("/v7/feature-flags/{flag_key}")
async def v72_upsert_feature_flag(flag_key: str, body: Dict[str, Any] | None = Body(default=None), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    try:
        return set_feature_flag_status(flag_key, body or {}, ctx)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/v7/feature-flags/{flag_key}/rollout")
async def v72_upsert_rollout_rule(flag_key: str, body: Dict[str, Any] | None = Body(default=None), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    try:
        return upsert_rollout_rule(flag_key, body or {}, ctx)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/v7/config-audits")
async def v73_config_audits(action: str | None = Query(default=None), target_key: str | None = Query(default=None), limit: int = Query(default=50, ge=1, le=200), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return config_audit_summary(ctx, action=action, target_key=target_key, limit=limit)


@router.get("/v7/config-audits/{audit_id}/compare")
async def v73_compare_config_audit(audit_id: str, ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    try:
        return compare_config_audit(audit_id, ctx)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/v7/config-audits/{audit_id}/rollback")
async def v73_rollback_config_audit(audit_id: str, ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    try:
        return rollback_config_audit(audit_id, ctx)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/v7/release-governance")
async def v74_release_governance(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return release_governance_summary(ctx)


@router.get("/v7/release-alerts")
async def v75_release_alerts(limit: int = Query(default=100, ge=1, le=300), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return release_alert_summary(ctx, limit=limit)


@router.post("/v7/release-alerts/generate")
async def v75_generate_release_alerts(body: Dict[str, Any] | None = Body(default=None), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    body = body or {}
    return generate_release_alerts(ctx, create_tasks=bool(body.get("createTasks") or body.get("create_tasks")))


@router.get("/v8/weight-snapshots")
async def v80_weight_snapshots(object_type: str | None = Query(default=None), limit: int = Query(default=120, ge=1, le=500), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return weight_snapshot_summary(ctx, object_type=object_type, limit=limit)


@router.post("/v8/weight-snapshots/generate")
async def v80_generate_weight_snapshots(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return generate_weight_snapshots(ctx)


@router.get("/v8/weight-comparisons")
async def v81_weight_comparisons(object_type: str | None = Query(default=None), comparison_type: str | None = Query(default=None), limit: int = Query(default=200, ge=1, le=800), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return weight_comparison_summary(ctx, object_type=object_type, comparison_type=comparison_type, limit=limit)


@router.post("/v8/weight-comparisons/generate")
async def v81_generate_weight_comparisons(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return generate_weight_comparisons(ctx)


@router.get("/v8/weight-rag-hits")
async def v82_weight_rag_hits(object_type: str | None = Query(default=None), hit_status: str | None = Query(default=None), limit: int = Query(default=200, ge=1, le=800), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return weight_rag_summary(ctx, object_type=object_type, hit_status=hit_status, limit=limit)


@router.post("/v8/weight-rag-hits/generate")
async def v82_generate_weight_rag_hits(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return generate_weight_rag_hits(ctx)


@router.get("/v8/linked-relations")
async def v83_linked_relations(object_type: str | None = Query(default=None), risk_direction: str | None = Query(default=None), limit: int = Query(default=200, ge=1, le=800), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return linked_relation_summary(ctx, object_type=object_type, risk_direction=risk_direction, limit=limit)


@router.post("/v8/linked-relations/generate")
async def v83_generate_linked_relations(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return generate_linked_metric_relations(ctx)


@router.get("/v8/weight-scores")
async def v84_weight_scores(object_type: str | None = Query(default=None), weight_state: str | None = Query(default=None), limit: int = Query(default=200, ge=1, le=800), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return weight_score_summary(ctx, object_type=object_type, weight_state=weight_state, limit=limit)


@router.post("/v8/weight-scores/generate")
async def v84_generate_weight_scores(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return generate_weight_scores(ctx)


@router.get("/context")
async def current_context(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return {"context": ctx.to_dict(), "auditMeta": ctx.audit_meta()}
