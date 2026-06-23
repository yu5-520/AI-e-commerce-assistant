"""V6.5 Trend Center routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, Query, Request

from src.services.account_service import current_user, user_id_from_headers
from src.services.high_risk_trend_gate_service import high_risk_gate_summary
from src.services.indicator_rag_service import indicator_rule_summary
from src.services.permission_budget_service import permission_budget_summary
from src.services.risk_task_v65_service import generate_risk_tasks_for_signals, risk_task_summary
from src.services.trend_signal_service import trend_center_summary

router = APIRouter(prefix="/api/trends", tags=["trends"])


@router.get("/summary")
def trends_summary(request: Request, limit: int = Query(default=30, ge=1, le=200)) -> Dict[str, Any]:
    """Return scoped trends, risk tasks, indicators, gates, and permission budgets."""
    user_id = user_id_from_headers(request.headers)
    summary = trend_center_summary(user_id=user_id, limit=limit)
    summary["riskTaskSummary"] = risk_task_summary(limit=limit)
    summary["indicatorRuleSummary"] = indicator_rule_summary(limit=limit)
    summary["highRiskGateSummary"] = high_risk_gate_summary(limit=limit)
    summary["permissionBudgetSummary"] = permission_budget_summary(limit=limit)
    summary["version"] = "6.5.0"
    summary["rule"] = "V6.5 趋势中心展示账号额度和审批链路；高风险通过门控后也只能按权限生成申请/审批任务。"
    return summary


@router.get("/risk-tasks")
def risk_tasks(limit: int = Query(default=30, ge=1, le=200)) -> Dict[str, Any]:
    """Return latest V6.5 risk task plans."""
    return risk_task_summary(limit=limit)


@router.post("/risk-tasks/generate")
def generate_risk_tasks(request: Request, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    """Regenerate risk-graded tasks with V6.5 permission budget gates."""
    body = body or {}
    user = current_user(user_id_from_headers(request.headers))
    role_id = body.get("requesterRoleId") or body.get("requester_role_id") or user.get("roleId") or "operator"
    return generate_risk_tasks_for_signals(data_version=body.get("dataVersion") or body.get("data_version"), limit=int(body.get("limit") or 200), requester_role_id=str(role_id))


@router.get("/indicator-rules")
def indicator_rules(limit: int = Query(default=50, ge=1, le=200)) -> Dict[str, Any]:
    """Return company RAG indicator rules and recent indicator matches."""
    return indicator_rule_summary(limit=limit)


@router.get("/high-risk-gates")
def high_risk_gates(limit: int = Query(default=50, ge=1, le=200)) -> Dict[str, Any]:
    """Return high-risk trend gate decisions."""
    return high_risk_gate_summary(limit=limit)


@router.get("/permission-budgets")
def permission_budgets(limit: int = Query(default=50, ge=1, le=200)) -> Dict[str, Any]:
    """Return permission budget limits and recent budget checks."""
    return permission_budget_summary(limit=limit)
