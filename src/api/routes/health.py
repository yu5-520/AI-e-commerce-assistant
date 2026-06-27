from typing import Any, Dict

from fastapi import APIRouter

API_VERSION = "11.15.0"
router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": API_VERSION,
        "product": "AI ERP Operating Advisor",
        "currentEntry": "/",
        "dashboardEntry": "/api/modules/dashboard",
        "operatingUnitEntry": "/api/modules/operating-unit",
        "runtimeDiagnosticsEntry": "/api/system/runtime-diagnostics",
        "runtimeResetEntry": "/api/system/reset-runtime-data?confirm=true",
        "repositoryModeEntry": "/api/system/repositories",
        "readinessEntry": "/api/architecture/v10/readiness",
    }
