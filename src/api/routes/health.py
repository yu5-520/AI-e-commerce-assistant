from typing import Any, Dict

from fastapi import APIRouter

API_VERSION = "11.9.0"
router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": API_VERSION,
        "product": "AI ERP Operating Advisor",
        "v98Entry": "/api/architecture/v9/ops-authorization",
        "v99Entry": "/api/architecture/v9/delivery-readiness",
        "v99ReadinessEntry": "/api/architecture/v9/readiness",
        "v100Entry": "/api/architecture/v10/task-driven-product",
        "v100ReadinessEntry": "/api/architecture/v10/readiness",
    }
