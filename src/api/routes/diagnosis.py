"""Diagnosis Center routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from src.services.workflow_service import run_full_workflow

router = APIRouter(prefix="/api/diagnosis", tags=["diagnosis"])


@router.post("/run")
def run_diagnosis() -> Dict[str, Any]:
    result = run_full_workflow(write_outputs=True, record_logs=True)
    return {
        "workflow_run_id": result.get("workflow_run_id"),
        "product_diagnosis": result["product_diagnosis"],
        "customer_segmentation": result["customer_segmentation"],
        "rag_context": result["rag_context"],
        "summary": result["summary"],
    }
