"""V6.8 Trend Center routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException, Query, Request

from src.services.account_service import current_user, user_id_from_headers
from src.services.approval_lifecycle_service import approval_lifecycle_summary, approve_flow, reject_flow
from src.services.execution_feedback_service import execution_feedback_summary, submit_execution_result
from src.services.high_risk_trend_gate_service import high_risk_gate_summary
from src.services.indicator_rag_service import indicator_rule_summary
from src.services.permission_budget_service import permission_budget_summary
from src.services.risk_task_v66_service import generate_risk_tasks_for_signals, risk_task_summary
from src.services.trend_signal_service import trend_center_summary

router = APIRouter(prefix="/api/trends", tags=["trends"])


@router.get("/summary")
def trends_summary(request: Request, limit: int = Query(default=30, ge=1, le=200)) -> Dict[str, Any]:
    user_id = user_id_from_headers(request.headers)
    user = current_user(user_id)
    summary = trend_center_summary(user_id=user_id, limit=limit)
    summary["riskTaskSummary"] = risk_task_summary(limit=limit)
    summary["indicatorRuleSummary"] = indicator_rule_summary(limit=limit)
    summary["highRiskGateSummary"] = high_risk_gate_summary(limit=limit)
    summary["permissionBudgetSummary"] = permission_budget_summary(limit=limit)
    summary["approvalLifecycleSummary"] = approval_lifecycle_summary(limit=limit)
    summary["executionFeedbackSummary"] = execution_feedback_summary(limit=limit)
    summary["approvalActionContext"] = {
        "version": "6.8.0",
        "currentRoleId": user.get("roleId"),
        "canApprove": user.get("roleId") in {"manager", "owner", "finance"},
        "canReject": user.get("roleId") in {"manager", "owner", "finance"},
        "canSubmitExecution": user.get("roleId") in {"operator", "manager", "owner"},
        "rule": "V6.8 前端可审批、驳回，并对审批通过后的执行任务提交结果回写。",
    }
    summary["version"] = "6.8.0"
    summary["rule"] = "V6.8 增加执行结果回写：审批通过后，执行任务需要提交实际花费、采购金额和证据。"
    return summary


@router.get("/risk-tasks")
def risk_tasks(limit: int = Query(default=30, ge=1, le=200)) -> Dict[str, Any]:
    return risk_task_summary(limit=limit)


@router.post("/risk-tasks/generate")
def generate_risk_tasks(request: Request, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    user = current_user(user_id_from_headers(request.headers))
    role_id = body.get("requesterRoleId") or body.get("requester_role_id") or user.get("roleId") or "operator"
    return generate_risk_tasks_for_signals(data_version=body.get("dataVersion") or body.get("data_version"), limit=int(body.get("limit") or 200), requester_role_id=str(role_id))


@router.get("/indicator-rules")
def indicator_rules(limit: int = Query(default=50, ge=1, le=200)) -> Dict[str, Any]:
    return indicator_rule_summary(limit=limit)


@router.get("/high-risk-gates")
def high_risk_gates(limit: int = Query(default=50, ge=1, le=200)) -> Dict[str, Any]:
    return high_risk_gate_summary(limit=limit)


@router.get("/permission-budgets")
def permission_budgets(limit: int = Query(default=50, ge=1, le=200)) -> Dict[str, Any]:
    return permission_budget_summary(limit=limit)


@router.get("/approval-flows")
def approval_flows(limit: int = Query(default=50, ge=1, le=200)) -> Dict[str, Any]:
    return approval_lifecycle_summary(limit=limit)


@router.post("/approval-flows/{flow_id}/approve")
def approve_approval_flow(request: Request, flow_id: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    role_id = body.get("approverRoleId") or body.get("approver_role_id") or current_user(user_id_from_headers(request.headers)).get("roleId") or "manager"
    try:
        return approve_flow(flow_id, str(role_id), note=body.get("note") or "前端审批通过。")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/approval-flows/{flow_id}/reject")
def reject_approval_flow(request: Request, flow_id: str, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    role_id = body.get("approverRoleId") or body.get("approver_role_id") or current_user(user_id_from_headers(request.headers)).get("roleId") or "manager"
    try:
        return reject_flow(flow_id, str(role_id), note=body.get("note") or "前端审批驳回。")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/execution-results")
def execution_results(limit: int = Query(default=50, ge=1, le=200)) -> Dict[str, Any]:
    return execution_feedback_summary(limit=limit)


@router.post("/execution-results")
def submit_execution_feedback(request: Request, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    role_id = current_user(user_id_from_headers(request.headers)).get("roleId") or "operator"
    return submit_execution_result(body, actor_role_id=str(role_id))
