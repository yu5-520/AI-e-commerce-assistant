"""V6.3 Trend Center, risk task, and RAG indicator routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, Query, Request

from src.services.account_service import user_id_from_headers
from src.services.indicator_rag_service import indicator_rule_summary
from src.services.risk_task_service import generate_risk_tasks_for_signals, risk_task_summary
from src.services.trend_signal_service import trend_center_summary

router = APIRouter(prefix="/api/trends", tags=["trends"])


@router.get("/summary")
def trends_summary(request: Request, limit: int = Query(default=30, ge=1, le=200)) -> Dict[str, Any]:
    """Return scoped product snapshots, metric trends, business signals, risk tasks, and RAG indicators."""
    summary = trend_center_summary(user_id=user_id_from_headers(request.headers), limit=limit)
    summary["riskTaskSummary"] = risk_task_summary(limit=limit)
    summary["indicatorRuleSummary"] = indicator_rule_summary(limit=limit)
    summary["version"] = "6.3.0"
    summary["rule"] = "V6.3 趋势中心展示快照、指标趋势、经营信号、风险分级任务和RAG指标门控。"
    return summary


@router.get("/risk-tasks")
def risk_tasks(limit: int = Query(default=30, ge=1, le=200)) -> Dict[str, Any]:
    """Return latest V6.3 risk task plans."""
    return risk_task_summary(limit=limit)


@router.post("/risk-tasks/generate")
def generate_risk_tasks(body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    """Regenerate risk-graded tasks from existing business signals with V6.3 RAG indicators."""
    body = body or {}
    return generate_risk_tasks_for_signals(data_version=body.get("dataVersion") or body.get("data_version"), limit=int(body.get("limit") or 200))


@router.get("/indicator-rules")
def indicator_rules(limit: int = Query(default=50, ge=1, le=200)) -> Dict[str, Any]:
    """Return company RAG indicator rules and recent indicator matches."""
    return indicator_rule_summary(limit=limit)
