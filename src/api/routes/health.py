"""Health routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

API_VERSION = "1.5.3"

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": API_VERSION,
        "product": "AI ERP Operating Advisor",
        "mode": "modular_backend_task_workflow",
        "api_entry": "/api/modules/*",
        "task_authority": "server_memory_mock",
        "task_identity_authority": "backend",
        "candidate_lifecycle": "pending_candidate_active_task_completed_archived",
        "route_structure": "split_module_files",
        "task_focus_navigation": True,
        "safety": {
            "real_erp_connected": False,
            "real_crm_connected": False,
            "real_shop_backend_connected": False,
            "auto_high_risk_execution": False,
        },
    }
