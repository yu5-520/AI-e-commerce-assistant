"""V6.4 Trend Center, risk task, RAG indicator, and gate routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, Query, Request

from src.services.account_service import user_id_from_headers
from src.services.high_risk_trend_gate_service import high_risk_gate_summary
from src.services.indicator_rag_service import indicator_rule_summary
from src.services.risk_task_service import generate_risk_tasks_for_signals, risk_task_summary
from src.services.trend_signal_service import trend_center_summary

router = APIRouter(prefix="/api/trends", tags=["trends"])


@router.get("/summary")
def trends_summary(request: Request, limit: int = Query(default=30, ge=1, le=200)) -> Dict[str, Any]:
    """Return scoped snapshots, trends, signals, risk tasks, indicators, and gates."""
    summary = trend_center_summary(user_id=user_id_from_headers(request.headers), limit=limit)
    summary["riskTaskSummary"] = risk_task_summary(limit=limit)
    summary["indicatorRuleSummary"] = indicator_rule_summary(limit=limit)
    summary["highRiskGateSummary"] = high_risk_gate_summary(limit=limit)
    summary["version"] = "6.4.0"
    summary["rule"] = "V6.4 趋势中心展示RAG指标门控和高风险历史趋势门控；通过后也只生成申请/审批任务。"
    return summary


@router.get("/risk-tasks")
def risk_tasks(limit: int = Query(default=30, ge=1, le=200)) -> Dict[str, Any]:
    """Return latest V6.4 risk task plans."""
    return risk_task_summary(limit=limit)


@router.post("/risk-tasks/generate")
def generate_risk_tasks(body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    """Regenerate risk-graded tasks with V6.4 high-risk gates."""
    body = body or {}
    return generate_risk_tasks_for_signals(data_version=body.get("dataVersion") or body.get("data_version"), limit=int(body.get("limit") or 200))


@router.get("/indicator-rules")
def indicator_rules(limit: int = Query(default=50, ge=1, le=200)) -> Dict[str, Any]:
    """Return company RAG indicator rules and recent indicator matches."""
    return indicator_rule_summary(limit=limit)


@router.get("/high-risk-gates")
def high_risk_gates(limit: int = Query(default=50, ge=1, le=200)) -> Dict[str, Any]:
    """Return high-risk trend gate decisions."""
    return high_risk_gate_summary(limit=limit)
