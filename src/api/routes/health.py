"""Health routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

API_VERSION = "9.7.0"
router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": API_VERSION,
        "product": "AI ERP Operating Advisor",
        "mode": "v970_audit_guard",
        "api_entry": "/api/modules/*",
        "account_entry": "/api/accounts",
        "v970_service": "src/services/v97_rag_audit_rollback_service.py",
    }
