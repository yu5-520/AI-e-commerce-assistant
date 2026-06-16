"""Health routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

API_VERSION = "1.3.0"

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": API_VERSION,
        "product": "AI ERP Operating Advisor",
        "mode": "mock_erp_crm_workflow",
        "safety": {
            "real_erp_connected": False,
            "real_crm_connected": False,
            "real_shop_backend_connected": False,
            "auto_high_risk_execution": False,
        },
    }
