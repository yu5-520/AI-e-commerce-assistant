"""Evals routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from src.services.eval_service import run_minimal_evals

router = APIRouter(prefix="/api/evals", tags=["evals"])


@router.get("/run")
def run_evals_api() -> Dict[str, Any]:
    return run_minimal_evals()
