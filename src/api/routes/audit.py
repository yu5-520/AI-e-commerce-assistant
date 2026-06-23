"""Trace, audit log, and technical log routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, Query

from src.core.context import UserContext, get_current_context
from src.services.tech_log_service import list_tech_logs, redact_sensitive_payload, tech_log_summary, write_tech_log
from src.services.trace_audit_service import audit_timeline, resolve_trace_id

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/traces/{trace_id}")
def trace_timeline(trace_id: str, limit: int = Query(default=100, ge=1, le=500), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Return one trace timeline from audit_logs."""

    return audit_timeline(ctx, trace_id=trace_id, limit=limit)


@router.get("/tech-logs")
def tech_logs(
    trace_id: str | None = Query(default=None),
    level: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    ctx: UserContext = Depends(get_current_context),
) -> Dict[str, Any]:
    """Return sanitized JSON technical logs."""

    return list_tech_logs(ctx, trace_id=trace_id, level=level, event_type=event_type, limit=limit)


@router.get("/tech-logs/summary")
def tech_logs_summary() -> Dict[str, Any]:
    """Return TechLog counts and redaction policy."""

    return tech_log_summary()


@router.post("/tech-logs/test-redaction")
def test_redaction(body: Dict[str, Any] = Body(default_factory=dict), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Write a test TechLog after redacting secrets from payload."""

    trace_id = resolve_trace_id(body, "TECHLOGTEST")
    redacted = redact_sensitive_payload(body)
    log = write_tech_log(
        ctx,
        trace_id=trace_id,
        level="info",
        logger="audit-api",
        event_type="tech_log.redaction_test",
        message="redaction test payload persisted",
        payload=body,
    )
    return {"version": log.get("version"), "traceId": trace_id, "redactedPayload": redacted, "techLog": log}
