"""Health routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

API_VERSION = "2.4.1"

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": API_VERSION,
        "product": "AI ERP Operating Advisor",
        "mode": "owner_business_overview_manager_dispatch_queue_layout",
        "api_entry": "/api/modules/*",
        "account_entry": "/api/accounts",
        "owner_business_overview": True,
        "owner_dashboard_not_task_list": True,
        "owner_module_entry_cards": True,
        "owner_attention_items": True,
        "store_overview": True,
        "people_overview": True,
        "supply_finance": True,
        "org_governance": True,
        "retrospective_audit": True,
        "basic_account_center": True,
        "manager_execution_dashboard": True,
        "manager_task_sorting": True,
        "manager_dispatch_queue_layout": True,
        "manager_task_detail": True,
        "manager_split_action": True,
        "manager_dispatch_action": True,
    }
