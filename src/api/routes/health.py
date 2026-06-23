"""Health routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from src.services.llm_provider_service import llm_status

API_VERSION = "9.6.0"
router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> Dict[str, Any]:
    llm = llm_status()
    return {
        "ok": True,
        "version": API_VERSION,
        "product": "AI ERP Operating Advisor",
        "mode": "v960_rag_write_memory",
        "api_entry": "/api/modules/*",
        "account_entry": "/api/accounts",
        "rag_write_memory_entry": "/api/architecture/v9/rag-write-memory",
        "rag_isolation_entry": "/api/architecture/v9/rag-isolation",
        "tier_isolation_entry": "/api/architecture/v9/tier-isolation",
        "safety": {
            "auto_platform_action": False,
            "auto_erp_crm_write": False,
            "auto_memory_promotion": False,
        },
        "v960_rag_write_memory": True,
        "v960_rag_write_service": "src/services/v96_rag_write_memory_service.py",
        "v960_memory_lifecycle": ["rag_memory_candidate", "quality_check", "namespace_policy_check", "human_review", "approval_decision", "promoted_memory", "audit_record"],
        "v950_rag_namespace_isolation": True,
        "v940_tier_isolation_consistency": True,
        "v930_frontend_module_consistency": True,
        "v920_backend_flow_consistency": True,
        "llm_enabled": llm.get("enabled"),
        "llm_ready": llm.get("ready"),
        "rag_memory_endpoint": "/api/modules/rag-memory",
        "rag_memory_search_endpoint": "/api/modules/rag-memory/search",
    }
