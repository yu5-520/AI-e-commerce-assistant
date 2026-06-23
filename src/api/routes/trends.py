"""V6.1 Trend Center routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Query, Request

from src.services.account_service import user_id_from_headers
from src.services.trend_signal_service import trend_center_summary

router = APIRouter(prefix="/api/trends", tags=["trends"])


@router.get("/summary")
def trends_summary(request: Request, limit: int = Query(default=30, ge=1, le=200)) -> Dict[str, Any]:
    """Return scoped product snapshots, metric trends, and business signals."""
    return trend_center_summary(user_id=user_id_from_headers(request.headers), limit=limit)
