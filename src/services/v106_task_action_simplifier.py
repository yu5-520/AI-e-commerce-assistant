"""V12.11.1 task action surface simplifier.

The task card exposes one current human action plus a persistent detail action.
Operator permission-in tasks are auto-accepted by the lifecycle state machine, so
operator cards normally show submit + detail instead of accept + detail.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

V106_TASK_ACTION_VERSION = "12.11.1"
V106_ROLE_ACTIONS = {
    "owner": ["view", "confirm"],
    "manager": ["approve", "reject"],
    "operator": ["accept", "submit", "supplement"],
    "finance": ["view"],
    "observer": ["view"],
}
V106_ACTION_RULES = [
    "one_current_human_action_per_task_card",
    "operator_permission_tasks_auto_accept_to_submit",
    "detail_action_is_persistent_and_not_workflow",
    "operator_cards_never_show_review_or_recap",
    "manager_cards_handle_review_only",
    "system_recap_stays_out_of_human_task_cards",
    "raw_available_actions_are_backend_only",
]

ACTION_LABELS = {"view": "查看", "confirm": "确认", "approve": "复核", "reject": "退回", "accept": "接收", "submit": "提交", "supplement": "补充", "detail": "详情"}
ROLE_SURFACE = {"owner": "progress", "manager": "review", "operator": "execution", "finance": "read_only", "observer": "read_only"}


def _role(task: Dict[str, Any]) -> str:
    role = task.get("viewerRoleId") or task.get("roleId") or task.get("currentRoleId") or "operator"
    return role if role in V106_ROLE_ACTIONS else "operator"


def _has(task: Dict[str, Any], action: str) -> bool:
    backend = set(task.get("availableActions") or [])
    status = str(task.get("status") or "")
    workflow = str(task.get("workflowStatus") or task.get("displayStatus") or "")
    lifecycle = str(task.get("lifecycleStage") or "")
    if action == "view":
        return True
    if action == "confirm":
        return status in {"已完成", "已通过", "已归档"} or workflow in {"复核通过", "已完成", "等待自动复盘"}
    if action in {"approve", "reject"}:
        return "review" in backend or status in {"已提交", "待复核"} or workflow in {"待复核", "待审批", "待老板确认"}
    if action == "accept":
        if status in {"处理中", "待复核", "已完成", "已通过", "已归档"} or workflow in {"处理中", "等待自动复盘"} or lifecycle in {"accepted", "evidence_submitted", "recap_scheduled"}:
            return False
        return "accept" in backend or status in {"待接收", "待确认", "已派发", "待处理", "待拆分"} or workflow in {"已派发", "待处理", "运营接收任务"}
    if action in {"submit", "supplement"}:
        return "submit" in backend or status in {"处理中", "已退回"} or workflow in {"处理中", "已退回"}
    return False


def _action(role: str, action: str, task: Dict[str, Any], *, primary: bool = False) -> Dict[str, Any]:
    return {"action": action, "label": ACTION_LABELS.get(action, action), "role": role, "primary": primary, "surface": ROLE_SURFACE.get(role, "execution"), "taskId": task.get("id")}


def simplified_actions_for_task(task: Dict[str, Any]) -> Dict[str, Any]:
    role = _role(task)
    allowed = [action for action in V106_ROLE_ACTIONS[role] if _has(task, action)]
    if role == "operator":
        allowed = [action for action in allowed if action in {"accept", "submit", "supplement"}]
    elif role == "manager":
        allowed = [action for action in allowed if action in {"approve", "reject"}]
    elif role in {"owner", "finance", "observer"}:
        allowed = [action for action in allowed if action in {"view", "confirm"}]
    primary = allowed[0] if allowed else None
    visible = [_action(role, primary, task, primary=True)] if primary else []
    raw = list(task.get("availableActions") or [])
    return {"version": V106_TASK_ACTION_VERSION, "role": role, "rules": V106_ACTION_RULES, "primaryAction": visible[0] if visible else None, "secondaryAction": None, "visibleActions": visible, "detailAction": _action(role, "detail", task, primary=False), "hiddenBackendActions": [item for item in raw if item not in {primary, "report", "source"}], "roleAllowedActions": V106_ROLE_ACTIONS[role], "rule": "V12.11.1：权限内运营任务自动接收后，任务卡只展示提交；详情常驻；复盘由系统自动执行。"}


def apply_v106_task_actions(task: Dict[str, Any]) -> Dict[str, Any]:
    item = deepcopy(task)
    simple = simplified_actions_for_task(item)
    item["taskActionVersion"] = V106_TASK_ACTION_VERSION
    item["simplifiedActions"] = simple
    item["primaryTaskAction"] = simple["primaryAction"]
    item["secondaryTaskAction"] = None
    item["visibleTaskActions"] = simple["visibleActions"]
    item["detailTaskAction"] = simple["detailAction"]
    return item
