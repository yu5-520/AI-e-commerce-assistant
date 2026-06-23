"""V9.8/V9.9 architecture readiness routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends

from src.core.context import UserContext, get_current_context
from src.services.v98_ops_authorization_service import ops_authorization_summary
from src.services.v99_delivery_readiness_service import delivery_readiness_summary

router = APIRouter(prefix="/api/architecture", tags=["architecture-v9-readiness"])


@router.get("/v9/ops-authorization")
async def v98_ops_authorization(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return ops_authorization_summary(ctx)


@router.get("/v9/delivery-readiness")
async def v99_delivery_readiness(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return delivery_readiness_summary(ctx)


@router.get("/v9/readiness")
async def v99_readiness_index(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return {
        "version": "9.9.0",
        "entries": {
            "opsAuthorization": "/api/architecture/v9/ops-authorization",
            "deliveryReadiness": "/api/architecture/v9/delivery-readiness",
        },
        "status": "v9_8_and_v9_9_routes_mounted",
        "context": ctx.to_dict(),
        "auditMeta": ctx.audit_meta(),
    }
