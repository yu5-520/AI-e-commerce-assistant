"""Health routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from src.services.llm_provider_service import llm_status

API_VERSION = "9.5.0"
router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> Dict[str, Any]:
    llm = llm_status()
    return {
        "ok": True,
        "version": API_VERSION,
        "product": "AI ERP Operating Advisor",
        "mode": "v950_rag_namespace_isolation",
        "api_entry": "/api/modules/*",
        "account_entry": "/api/accounts",
        "architecture_entry": "/api/architecture/v9/backend-flow",
        "frontend_module_entry": "/api/architecture/v9/frontend-modules",
        "tier_isolation_entry": "/api/architecture/v9/tier-isolation",
        "rag_isolation_entry": "/api/architecture/v9/rag-isolation",
        "safety": {
            "auto_platform_action": False,
            "auto_erp_crm_write": False,
            "marketplace_api_connected": False,
        },
        "v950_rag_namespace_isolation": True,
        "v950_rag_isolation_service": "src/services/v95_rag_namespace_isolation_service.py",
        "v950_namespaces": ["shared_desensitized_rag", "tenant_isolated_rag", "private_customer_rag"],
        "v950_access_gates": ["namespaceResolver", "ingestionGate", "retrievalGate", "writeGate", "templateMaintenanceGate", "deletionGate"],
        "v940_tier_isolation_consistency": True,
        "v930_frontend_module_consistency": True,
        "v920_backend_flow_consistency": True,
        "llm_enabled": llm.get("enabled"),
        "llm_ready": llm.get("ready"),
        "rag_memory_endpoint": "/api/modules/rag-memory",
        "rag_memory_search_endpoint": "/api/modules/rag-memory/search",
    }
