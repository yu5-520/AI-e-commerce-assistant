"""Health routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": "Product API MVP",
        "mode": "mock_workflow_only",
        "safety": {
            "real_erp_connected": False,
            "real_crm_connected": False,
            "real_shop_backend_connected": False,
            "auto_high_risk_execution": False,
        },
    }
