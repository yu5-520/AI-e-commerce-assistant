"""Trace and audit log routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, Query

from src.core.context import UserContext, get_current_context
from src.services.trace_audit_service import audit_timeline

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/traces/{trace_id}")
def trace_timeline(trace_id: str, limit: int = Query(default=100, ge=1, le=500), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Return one trace timeline from audit_logs."""

    return audit_timeline(ctx, trace_id=trace_id, limit=limit)
