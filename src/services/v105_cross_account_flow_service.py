"""V10.5 cross-account task flow contract.

A task is still one business event. V10.5 adds role-specific display status,
primary actions and sync targets so owner, manager and operator accounts see
the same task in the right product language without manually choosing workflow nodes.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

V105_CROSS_ACCOUNT_FLOW_VERSION = "10.5.0"
V105_ROLES = ["owner", "manager", "operator"]
V105_FLOW_RULES = [
    "one_task_id_multiple_role_views",
    "operator_submit_routes_to_manager_review",
    "manager_review_routes_to_owner_progress",
    "owner_sees_progress_not_operations",
    "all_transitions_write_events_and_logs",
]

OWNER_STATUS_MAP = {
    "待接收": "待处理",
    "已派发": "待处理",
    "处理中": "处理中",
    "已提交": "待复核",
    "待复核": "待复核",
    "已退回": "需补充",
    "已完成": "已完成",
    "复核通过": "已完成",
    "已归档": "已完成",
}

MANAGER_STATUS_MAP = {
    "待拆分": "待派发",
    "待接收": "已派发",
    "已派发": "已派发",
    "处理中": "处理中",
    "已提交": "待复核",
    "待复核": "待复核",
    "已退回": "已驳回",
    "已完成": "已完成",
    "复核通过": "已完成",
    "已归档": "已归档",
}

OPERATOR_STATUS_MAP = {
    "待拆分": "待接收",
    "待接收": "待接收",
    "已派发": "待接收",
    "处理中": "处理中",
    "已提交": "已提交",
    "待复核": "待复核",
    "已退回": "需补充",
    "已完成": "已完成",
    "复核通过": "已完成",
    "已归档": "已完成",
}


def _status(task: Dict[str, Any]) -> str:
    return str(task.get("status") or task.get("workflowStatus") or "待接收")


def _workflow(task: Dict[str, Any]) -> str:
    return str(task.get("workflowStatus") or task.get("status") or "待接收")


def _owner_actions(task: Dict[str, Any]) -> List[str]:
    status = _status(task)
    if status in {"已完成", "已通过", "已归档"} or _workflow(task) in {"复核通过", "已完成"}:
        return ["view", "confirm"]
    return ["view", "follow"]


def _manager_actions(task: Dict[str, Any]) -> List[str]:
    status = _status(task)
    workflow = _workflow(task)
    if status in {"待拆分", "待派发"} or workflow in {"待拆分", "待派发"}:
        return ["dispatch"]
    if status in {"已提交", "待复核"} or workflow == "待复核":
        return ["approve", "reject"]
    if status in {"已完成", "已通过"} or workflow in {"复核通过", "已完成"}:
        return ["archive"]
    return ["view_progress"]


def _operator_actions(task: Dict[str, Any]) -> List[str]:
    status = _status(task)
    workflow = _workflow(task)
    if status in {"待接收", "待确认", "已派发"} or workflow == "已派发":
        return ["accept"]
    if status in {"处理中", "已退回"} or workflow in {"处理中", "已退回"}:
        return ["submit", "supplement"]
    return ["view"]


def role_display_status(task: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    status = _status(task)
    workflow = _workflow(task)
    return {
        "owner": {
            "displayStatus": OWNER_STATUS_MAP.get(status) or OWNER_STATUS_MAP.get(workflow) or status,
            "primaryActions": _owner_actions(task),
            "surface": "progress",
            "summary": "看风险、负责人、进度和结果。",
        },
        "manager": {
            "displayStatus": MANAGER_STATUS_MAP.get(status) or MANAGER_STATUS_MAP.get(workflow) or status,
            "primaryActions": _manager_actions(task),
            "surface": "dispatch_review",
            "summary": "看派发、处理中、待复核和驳回。",
        },
        "operator": {
            "displayStatus": OPERATOR_STATUS_MAP.get(status) or OPERATOR_STATUS_MAP.get(workflow) or status,
            "primaryActions": _operator_actions(task),
            "surface": "execution",
            "summary": "看接收、提交、补充和完成。",
        },
    }


def next_sync_target(task: Dict[str, Any]) -> Dict[str, Any]:
    status = _status(task)
    workflow = _workflow(task)
    if status in {"待接收", "已派发"} or workflow == "已派发":
        return {"role": "operator", "label": "运营待接收", "reason": "任务已派发到执行账号。"}
    if status == "处理中" or workflow == "处理中":
        return {"role": "operator", "label": "运营处理中", "reason": "任务正在执行，老板和总管同步看进度。"}
    if status in {"已提交", "待复核"} or workflow == "待复核":
        return {"role": "manager", "label": "总管待复核", "reason": "运营提交后自动进入总管复核。"}
    if status in {"已退回"} or workflow == "已退回":
        return {"role": "operator", "label": "运营需补充", "reason": "总管驳回后自动回到运营补充。"}
    if status in {"已完成", "已通过"} or workflow in {"复核通过", "已完成"}:
        return {"role": "owner", "label": "老板看结果", "reason": "复核通过后老板同步看到完成结果。"}
    return {"role": "manager", "label": "总管跟进", "reason": "任务进入管理跟进。"}


def v105_visible_roles(task: Dict[str, Any]) -> List[str]:
    roles = set(task.get("visibleRoleIds") or [])
    roles.update({"owner", "manager"})
    layer = task.get("taskLayer")
    if layer in {"operator_execution", "finance_check"} or task.get("assigneeId"):
        roles.add("operator")
    if layer == "finance_check" or task.get("riskDomain") in {"报表", "价格", "流量", "库存", "利润", "财务"}:
        roles.add("finance")
    return [role for role in ["owner", "manager", "operator", "finance", "observer"] if role in roles]


def apply_v105_cross_account_flow(task: Dict[str, Any]) -> Dict[str, Any]:
    item = task
    item["crossAccountFlowVersion"] = V105_CROSS_ACCOUNT_FLOW_VERSION
    item["crossAccountFlow"] = {
        "mode": "one_task_id_multiple_role_views",
        "roles": V105_ROLES,
        "rules": V105_FLOW_RULES,
        "nextSyncTarget": next_sync_target(item),
    }
    item["roleViewStatus"] = role_display_status(item)
    item["displayStatusByRole"] = {role: view["displayStatus"] for role, view in item["roleViewStatus"].items()}
    item["primaryActionsByRole"] = {role: view["primaryActions"] for role, view in item["roleViewStatus"].items()}
    item["visibleRoleIds"] = v105_visible_roles(item)
    return item


def projected_task_for_role(task: Dict[str, Any], role_id: str | None) -> Dict[str, Any]:
    item = deepcopy(task)
    role = role_id or "operator"
    view = (item.get("roleViewStatus") or {}).get(role) or (item.get("roleViewStatus") or {}).get("operator") or {}
    item["displayStatus"] = view.get("displayStatus") or item.get("status")
    item["primaryRoleActions"] = view.get("primaryActions") or item.get("availableActions") or []
    item["roleSurface"] = view.get("surface") or "execution"
    item["roleSummary"] = view.get("summary") or "按当前账号处理任务。"
    return item
