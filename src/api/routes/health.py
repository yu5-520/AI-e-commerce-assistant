from typing import Any, Dict

from fastapi import APIRouter

API_VERSION = "9.9.0"
router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "version": API_VERSION, "product": "AI ERP Operating Advisor"}
