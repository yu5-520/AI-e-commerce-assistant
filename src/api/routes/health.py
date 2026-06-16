"""Health routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

API_VERSION = "2.2.0"

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": API_VERSION,
        "product": "AI ERP Operating Advisor",
        "mode": "executive_navigation_role_console_workflow",
        "api_entry": "/api/modules/*",
        "account_entry": "/api/accounts",
        "task_authority": "server_memory_mock",
        "task_identity_authority": "backend",
        "account_system": "v2_mock_rbac_switchable",
        "account_switch_header": "X-Mock-User-Id",
        "executive_navigation": True,
        "role_console": True,
        "insight_depth": "role_based",
        "task_assignment_flow": "task_pool_assigned_submitted_reviewed_archived",
        "task_report_page": True,
        "candidate_report_cta": True,
        "candidate_lifecycle": "pending_candidate_active_task_completed_archived",
        "route_structure": "split_module_files",
        "task_focus_navigation": True,
        "safety": {
            "real_erp_connected": False,
            "real_crm_connected": False,
            "real_shop_backend_connected": False,
            "real_sso_connected": False,
            "auto_high_risk_execution": False,
        },
    }
