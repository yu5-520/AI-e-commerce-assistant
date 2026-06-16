"""Health routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

API_VERSION = "2.3.9"

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": API_VERSION,
        "product": "AI ERP Operating Advisor",
        "mode": "owner_overview_manager_task_action_loop",
        "api_entry": "/api/modules/*",
        "account_entry": "/api/accounts",
        "store_overview": True,
        "people_overview": True,
        "supply_finance": True,
        "org_governance": True,
        "retrospective_audit": True,
        "basic_account_center": True,
        "manager_execution_dashboard": True,
        "manager_task_intake": True,
        "manager_task_sorting": True,
        "manager_task_detail": True,
        "manager_agent_judgment_placeholder": True,
        "manager_split_action": True,
        "manager_dispatch_action": True,
        "manager_review": True,
        "manager_retrospective_submit": True,
        "manager_reports": True,
    }
