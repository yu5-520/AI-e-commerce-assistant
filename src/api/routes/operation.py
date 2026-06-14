"""Product-facing routes for the AI operation advisor.

These routes are meant for the UI and product demo. They avoid exposing internal
terms such as workflow nodes, logs, RAG internals, or SQLite tables.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from src.services.product_api_service import (
    build_actions_payload,
    build_competitors_payload,
    build_data_check_payload,
    build_listing_payload,
    build_operating_unit_payload,
    build_operation_payload,
    build_products_payload,
    build_today_payload,
    build_traffic_payload,
    run_operation_cycle,
)
from src.services.workflow_service import get_demo_report_text

router = APIRouter(prefix="/api/operation", tags=["operation"])


@router.get("/today")
def today_overview() -> Dict[str, Any]:
    """Return the full merchant-facing operation payload for the current cycle."""
    result = run_operation_cycle(write_outputs=True, record_logs=True)
    return build_operation_payload(result)


@router.get("/summary")
def operation_summary() -> Dict[str, Any]:
    """Return only the top-level today overview cards."""
    result = run_operation_cycle(write_outputs=True, record_logs=True)
    return build_today_payload(result)


@router.get("/operating-unit")
def operating_unit() -> Dict[str, Any]:
    """Return ERP-inferred operating unit and cycle policy."""
    result = run_operation_cycle(write_outputs=False, record_logs=False)
    return build_operating_unit_payload(result)


@router.get("/data-check")
def data_check() -> Dict[str, Any]:
    """Return merchant-facing data readiness summary."""
    result = run_operation_cycle(write_outputs=False, record_logs=False)
    return build_data_check_payload(result)


@router.get("/products")
def product_checkup() -> Dict[str, Any]:
    """Return product checkup results."""
    result = run_operation_cycle(write_outputs=False, record_logs=False)
    return build_products_payload(result)


@router.get("/competitors")
def competitor_opportunities() -> Dict[str, Any]:
    """Return same-operating-unit competitor opportunity summary."""
    result = run_operation_cycle(write_outputs=False, record_logs=False)
    return build_competitors_payload(result)


@router.get("/listing")
def listing_suggestions() -> Dict[str, Any]:
    """Return same-operating-unit listing growth suggestions."""
    result = run_operation_cycle(write_outputs=False, record_logs=False)
    return build_listing_payload(result)


@router.get("/traffic")
def traffic_review() -> Dict[str, Any]:
    """Return traffic test review and loopback actions."""
    result = run_operation_cycle(write_outputs=False, record_logs=False)
    return build_traffic_payload(result)


@router.get("/actions")
def pending_actions() -> Dict[str, Any]:
    """Return pending actions that require human confirmation."""
    result = run_operation_cycle(write_outputs=False, record_logs=False)
    return build_actions_payload(result)


@router.get("/report", response_class=PlainTextResponse)
def operation_report() -> str:
    """Return the latest merchant-facing operation report."""
    return get_demo_report_text()
