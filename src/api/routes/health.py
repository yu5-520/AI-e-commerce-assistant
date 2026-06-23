from typing import Any, Dict

from fastapi import APIRouter, Depends

from src.core.context import UserContext, get_current_context
from src.services.v98_ops_authorization_service import ops_authorization_summary
from src.services.v99_delivery_readiness_service import delivery_readiness_summary

API_VERSION = "9.9.0"
router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": API_VERSION,
        "product": "AI ERP Operating Advisor",
        "v98Entry": "/api/architecture/v9/ops-authorization",
        "v99Entry": "/api/architecture/v9/delivery-readiness",
    }


@router.get("/architecture/v9/ops-authorization")
def v98_ops_authorization(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return ops_authorization_summary(ctx)


@router.get("/architecture/v9/delivery-readiness")
def v99_delivery_readiness(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return delivery_readiness_summary(ctx)
