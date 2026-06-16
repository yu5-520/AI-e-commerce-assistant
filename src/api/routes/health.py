"""Health routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

API_VERSION = "2.3.3"

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": API_VERSION,
        "product": "AI ERP Operating Advisor",
        "mode": "store_people_supply_finance_overview",
        "api_entry": "/api/modules/*",
        "account_entry": "/api/accounts",
        "store_overview": True,
        "people_overview": True,
        "supply_finance": True,
        "role_console": True,
    }
