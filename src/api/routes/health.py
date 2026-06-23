"""Health routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

API_VERSION = "9.8.0"
router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": API_VERSION,
        "product": "AI ERP Operating Advisor",
        "mode": "v980_ops_auth_guard",
        "api_entry": "/api/modules/*",
        "account_entry": "/api/accounts",
        "v980_service": "src/services/v98_ops_authorization_service.py",
        "v980_roles": ["owner_high_level", "business_manager", "operator", "external_ops_admin", "audit_observer"],
    }
