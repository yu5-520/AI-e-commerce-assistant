"""Customer Center routes."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from src.services.workflow_service import get_customer, get_customers

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("")
def list_customers() -> List[Dict[str, Any]]:
    return get_customers()


@router.get("/segments")
def customer_segments() -> Dict[str, Any]:
    customers = get_customers()
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for customer in customers:
        grouped.setdefault(str(customer.get("segment", "unknown")), []).append(customer)
    return {
        "segment_count": len(grouped),
        "segments": grouped,
    }


@router.get("/{customer_id}")
def customer_detail(customer_id: str) -> Dict[str, Any]:
    customer = get_customer(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail=f"Customer not found: {customer_id}")
    return customer
