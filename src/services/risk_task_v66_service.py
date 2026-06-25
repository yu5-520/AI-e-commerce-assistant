"""V11.8 risk task wrapper with approval lifecycle sync."""

from __future__ import annotations

from typing import Any, Dict

from src.services.approval_lifecycle_service import create_approval_flow_for_task, ensure_approval_lifecycle_tables
from src.services.risk_task_v65_service import ensure_risk_task_tables, risk_task_summary as _risk_task_summary
from src.services.risk_task_v65_service import generate_risk_tasks_for_signals as _generate_v65

RISK_TASK_VERSION = "11.8.0"


def generate_risk_tasks_for_signals(data_version: str | None = None, limit: int = 200, requester_role_id: str = "operator") -> Dict[str, Any]:
    """Generate V11.8 SOP task packages, then attach approval flows to executable tasks."""
    ensure_risk_task_tables()
    ensure_approval_lifecycle_tables()
    result = _generate_v65(data_version=data_version, limit=limit, requester_role_id=requester_role_id)
    flows = []
    for task in result.get("tasks") or []:
        budget = task.get("permissionBudgetGate") or {}
        if task.get("queueType") in {"urgent_execution", "today_execution"} and (task.get("riskGrade") == "高" or budget.get("needsApproval") or task.get("approvalChain")):
            flows.append(create_approval_flow_for_task(task, requester_role_id=requester_role_id))
    result["version"] = RISK_TASK_VERSION
    result["mode"] = "v11_8_ownership_first_sop_task_generation"
    result["approvalLifecycleSync"] = {
        "version": RISK_TASK_VERSION,
        "createdFlowCount": len(flows),
        "flows": flows,
        "rule": "V11.8 只有结构化 SOP 任务包进入审批生命周期；任务继承经营对象权限。",
    }
    result["rule"] = "上传账号决定经营对象归属，经营对象归属决定任务派发，旧规则不得生成新任务。"
    return result


def risk_task_summary(limit: int = 30) -> Dict[str, Any]:
    summary = _risk_task_summary(limit=limit)
    summary["version"] = RISK_TASK_VERSION
    return summary
