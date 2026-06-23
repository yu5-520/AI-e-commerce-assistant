"""V6.6 risk task wrapper with approval lifecycle sync."""

from __future__ import annotations

from typing import Any, Dict

from src.services.approval_lifecycle_service import create_approval_flow_for_task, ensure_approval_lifecycle_tables
from src.services.risk_task_v65_service import ensure_risk_task_tables, risk_task_summary as _risk_task_summary
from src.services.risk_task_v65_service import generate_risk_tasks_for_signals as _generate_v65

RISK_TASK_VERSION = "6.6.0"


def generate_risk_tasks_for_signals(data_version: str | None = None, limit: int = 200, requester_role_id: str = "operator") -> Dict[str, Any]:
    """Generate V6.5 risk tasks, then attach V6.6 approval lifecycle flows."""
    ensure_risk_task_tables()
    ensure_approval_lifecycle_tables()
    result = _generate_v65(data_version=data_version, limit=limit, requester_role_id=requester_role_id)
    flows = []
    for task in result.get("tasks") or []:
        budget = task.get("permissionBudgetGate") or {}
        if task.get("riskGrade") == "高" or budget.get("needsApproval") or task.get("approvalChain"):
            flows.append(create_approval_flow_for_task(task, requester_role_id=requester_role_id))
    result["version"] = RISK_TASK_VERSION
    result["mode"] = "approval_lifecycle_task_generation"
    result["approvalLifecycleSync"] = {
        "version": RISK_TASK_VERSION,
        "createdFlowCount": len(flows),
        "flows": flows,
        "rule": "V6.6 申请和执行分离：申请任务进入审批生命周期，审批通过后再生成执行任务。",
    }
    result["rule"] = "V6.6 运营申请、总管/老板审批、审批通过后再拆成执行任务；高风险不能自动执行。"
    return result


def risk_task_summary(limit: int = 30) -> Dict[str, Any]:
    summary = _risk_task_summary(limit=limit)
    summary["version"] = RISK_TASK_VERSION
    return summary
