"""Data Hub routes."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

from src.services.data_import_service import (
    import_mock_data,
    list_import_records,
    list_import_sources,
    validate_all_imports,
)

router = APIRouter(prefix="/api/data", tags=["data-import"])


@router.get("/sources")
def data_sources() -> List[Dict[str, Any]]:
    """List available Mock ERP / CRM import sources."""
    return list_import_sources()


@router.post("/validate")
def validate_imports() -> Dict[str, Any]:
    """Validate all Mock ERP / CRM datasets and relationship checks."""
    return validate_all_imports()


@router.post("/import/mock")
def import_mock() -> Dict[str, Any]:
    """Create an import record for current Mock datasets after validation."""
    return import_mock_data()


@router.get("/imports")
def imports() -> List[Dict[str, Any]]:
    """List recent import records."""
    return list_import_records()
