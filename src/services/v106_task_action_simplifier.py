"""V10.6 task action simplifier.

The task system may keep rich backend workflow actions, but the product surface
must expose only the smallest useful action set for the current role.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

V106_TASK_ACTION_VERSION = "10.6.0"
V106_ROLE_ACTIONS = {
    "owner": ["view", "follow", "confirm"],
    "manager": ["dispatch", "approve", "reject"],
    "operator": ["accept", "submit", "supplement"],
}
V106_ACTION_RULES = [
    "one_primary_action_per_task_card",
    "one_secondary_action_allowed",
    "details_are_not_workflow_actions",
    "debug_actions_stay_out_of_daily_task_cards",
    "backend_keeps_full_events_and_logs",
]

ACTION_LABELS = {
    "view": "查看",
    "follow": "关注",
    "confirm": "确认",
    "dispatch": "派发",
    "approve": "通过",
    "reject": "驳回",
    "accept": "接收",
    "submit": "提交",
    "supplement": "补充",
}

ROLE_SURFACE = {
    "owner": "progress",
    "manager": "dispatch_review",
    "operator": "execution",
}


def _role(task: Dict[str, Any]) -> str:
    role = task.get("viewerRoleId") or task.get("roleId") or "operator"
    return role if role in V106_ROLE_ACTIONS else "operator"


def _has(task: Dict[str, Any], action: str) -> bool:
    backend = set(task.get("availableActions") or [])
    status = str(task.get("status") or "")
    workflow = str(task.get("workflowStatus") or "")
    if action == "view":
        return True
    if action == "follow":
        return status not in {"已完成", "已归档"}
    if action == "confirm":
        return status in {"已完成", "已通过", "已归档"} or workflow in {"复核通过", "已完成"}
    if action == "dispatch":
        return "assign" in backend or status in {"待拆分", "待派发"}
    if action in {"approve", "reject"}:
        return "review" in backend or status in {"已提交", "待复核"} or workflow == "待复核"
    if action == "accept":
        return "accept" in backend or status in {"待接收", "待确认", "已派发"} or workflow == "已派发"
    if action in {"submit", "supplement"}:
        return "submit" in backend or status in {"处理中", "已退回"} or workflow in {"处理中", "已退回"}
    return action in backend


def _action(role: str, action: str, task: Dict[str, Any], *, primary: bool = False) -> Dict[str, Any]:
    return {
        "action": action,
        "label": ACTION_LABELS.get(action, action),
        "role": role,
        "primary": primary,
        "surface": ROLE_SURFACE.get(role, "execution"),
    }


def simplified_actions_for_task(task: Dict[str, Any]) -> Dict[str, Any]:
    role = _role(task)
    allowed = [action for action in V106_ROLE_ACTIONS[role] if _has(task, action)]
    if not allowed:
        allowed = ["view"] if role == "owner" else []
    primary = allowed[0] if allowed else None
    secondary = allowed[1] if len(allowed) > 1 else None
    return {
        "version": V106_TASK_ACTION_VERSION,
        "role": role,
        "rules": V106_ACTION_RULES,
        "primaryAction": _action(role, primary, task, primary=True) if primary else None,
        "secondaryAction": _action(role, secondary, task) if secondary else None,
        "visibleActions": [_action(role, action, task, primary=(action == primary)) for action in allowed[:2]],
        "hiddenBackendActions": [item for item in (task.get("availableActions") or []) if item not in allowed[:2]],
        "roleAllowedActions": V106_ROLE_ACTIONS[role],
    }


def apply_v106_task_actions(task: Dict[str, Any]) -> Dict[str, Any]:
    item = deepcopy(task)
    simple = simplified_actions_for_task(item)
    item["taskActionVersion"] = V106_TASK_ACTION_VERSION
    item["simplifiedActions"] = simple
    item["primaryTaskAction"] = simple["primaryAction"]
    item["secondaryTaskAction"] = simple["secondaryAction"]
    item["visibleTaskActions"] = simple["visibleActions"]
    return item
