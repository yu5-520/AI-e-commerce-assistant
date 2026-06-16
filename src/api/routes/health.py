"""Health routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

API_VERSION = "2.3.7"

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": API_VERSION,
        "product": "AI ERP Operating Advisor",
        "mode": "store_people_supply_finance_org_retrospective_basic_account_center",
        "api_entry": "/api/modules/*",
        "account_entry": "/api/accounts",
        "store_overview": True,
        "people_overview": True,
        "supply_finance": True,
        "org_governance": True,
        "retrospective_audit": True,
        "basic_account_center": True,
        "account_security_settings": True,
        "account_binding_settings": True,
        "account_notification_settings": True,
    }
