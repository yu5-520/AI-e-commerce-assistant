"""Trend Center routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException, Query, Request

from src.services.account_service import current_user, user_id_from_headers
from src.services.approval_lifecycle_service import approval_lifecycle_summary, approve_flow, reject_flow
from src.services.execution_feedback_service import execution_feedback_summary, submit_execution_result
from src.services.execution_review_service import create_review_from_execution_result, execution_review_summary, generate_reviews_for_recent_results
from src.services.high_risk_trend_gate_service import high_risk_gate_summary
from src.services.indicator_rag_service import indicator_rule_summary
from src.services.permission_budget_service import permission_budget_summary
from src.services.risk_task_v66_service import generate_risk_tasks_for_signals, risk_task_summary
from src.services.trend_signal_service import trend_center_summary
from src.services.v1012_metric_trend_evidence_service import build_metric_trend_evidence
from src.services.v1013_task_sop_engine_service import build_task_sop

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
    summary["executionReviewSummary"] = execution_review_summary(limit=limit)
    summary["v1012MetricTrendEvidence"] = {
        "version": "10.12.0",
        "entry": "/api/trends/metric-evidence",
        "rule": "精准指标是信任底线；单点只记录，趋势和交叉验证决定任务；权重只作为高级升维层。",
    }
    summary["v1013TaskSopEngine"] = {
        "version": "10.13.0",
        "entry": "/api/trends/task-sop",
        "rule": "SOP 是骨架，公司 RAG 是调参，指标趋势是证据，复核标准是闭环。",
    }
    summary["approvalActionContext"] = {
        "version": "6.9.0",
        "currentRoleId": user.get("roleId"),
        "canApprove": user.get("roleId") in {"manager", "owner", "finance"},
        "canReject": user.get("roleId") in {"manager", "owner", "finance"},
        "canSubmitExecution": user.get("roleId") in {"operator", "manager", "owner"},
        "canCreateReview": user.get("roleId") in {"manager", "owner", "finance"},
        "rule": "V6.9 前端可把执行回写转成复盘案例和RAG记忆。",
    }
    summary["version"] = "6.9.0"
    summary["rule"] = "趋势中心展示总店铺、单商品、平台、类目的趋势支撑；V10.13 增加任务 SOP 执行工单。"
    return summary


@router.post("/metric-evidence")
def metric_trend_evidence(body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    source_payload = body.get("sourcePayload") or body.get("source_payload") or body
    metrics = body.get("metrics") or {}
    return build_metric_trend_evidence(
        source_payload,
        metrics=metrics,
        category_id=body.get("categoryId") or source_payload.get("categoryId"),
        platform=body.get("platform") or source_payload.get("platform"),
        product_stage=body.get("productStage") or source_payload.get("productStage"),
    )


@router.post("/task-sop")
def task_sop(body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    return build_task_sop(
        body.get("problemType") or body.get("problem_type") or "general_operation",
        task_decision=body.get("taskDecision") or body.get("task_decision") or {},
        metric_evidence=body.get("metricEvidence") or body.get("metric_evidence") or {},
        rag_items=body.get("ragItems") or body.get("rag_items") or [],
        company_policy=body.get("companyPolicy") or body.get("company_policy") or {},
    )


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


@router.get("/execution-reviews")
def execution_reviews(limit: int = Query(default=50, ge=1, le=200)) -> Dict[str, Any]:
    return execution_review_summary(limit=limit)


@router.post("/execution-reviews/generate")
def generate_execution_reviews(request: Request, body: Dict[str, Any] | None = Body(default=None)) -> Dict[str, Any]:
    body = body or {}
    role_id = current_user(user_id_from_headers(request.headers)).get("roleId") or "manager"
    if body.get("executionResultId") or body.get("execution_result_id"):
        try:
            return create_review_from_execution_result(str(body.get("executionResultId") or body.get("execution_result_id")), actor_role_id=str(role_id), note=body.get("note"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    return generate_reviews_for_recent_results(limit=int(body.get("limit") or 30), actor_role_id=str(role_id))
