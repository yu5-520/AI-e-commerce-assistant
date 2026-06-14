"""Product Center routes."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from src.services.workflow_service import get_product, get_products

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("")
def list_products() -> List[Dict[str, Any]]:
    return get_products()


@router.get("/{product_id}")
def product_detail(product_id: str) -> Dict[str, Any]:
    product = get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail=f"Product not found: {product_id}")
    return product


@router.get("/{product_id}/diagnosis")
def product_diagnosis(product_id: str) -> Dict[str, Any]:
    product = get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail=f"Product not found: {product_id}")
    return {
        "target_type": "product",
        "target_id": product_id,
        "diagnosis": product,
    }
