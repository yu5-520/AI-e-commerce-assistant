"""Productized business routes for the AI ERP operating advisor UI.

These endpoints wrap the internal workflow result with merchant-facing names.
They are the only product-facing business API consumed by the current frontend.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from src.services.approval_service import get_task_status_overrides
from src.services.business_view_service import (
    get_action_confirmations,
    get_business_report_text,
    get_competitor_opportunities,
    get_data_health,
    get_listing_suggestions,
    get_operating_unit_view,
    get_product_health,
    get_today_advice,
    get_traffic_review,
)

router = APIRouter(prefix="/api/business", tags=["business"])


@router.get("/today")
def today_advice() -> Dict[str, Any]:
    """Return the merchant-facing daily overview."""
    payload = get_today_advice(write_outputs=True, record_logs=True)
    overrides = get_task_status_overrides()
    if overrides:
        payload["action_status_overrides"] = overrides
    return payload


@router.get("/operating-unit")
def operating_unit() -> Dict[str, Any]:
    """Return ERP-inferred operating unit and cycle policy."""
    return get_operating_unit_view()


@router.get("/data-health")
def data_health() -> Dict[str, Any]:
    """Return data readiness summary for productized UI."""
    return get_data_health()


@router.get("/products")
def products() -> Dict[str, Any]:
    """Return product health cards."""
    return get_product_health()


@router.get("/competitors")
def competitors() -> Dict[str, Any]:
    """Return same-operating-unit competitor opportunities."""
    return get_competitor_opportunities()


@router.get("/listing")
def listing() -> Dict[str, Any]:
    """Return listing growth suggestions."""
    return get_listing_suggestions()


@router.get("/traffic")
def traffic() -> Dict[str, Any]:
    """Return traffic test review and loopback actions."""
    return get_traffic_review()


@router.get("/actions")
def actions() -> Dict[str, List[Dict[str, Any]]]:
    """Return actions that require merchant confirmation."""
    return get_action_confirmations()


@router.get("/report", response_class=PlainTextResponse)
def report() -> str:
    """Return latest business report text."""
    return get_business_report_text()
