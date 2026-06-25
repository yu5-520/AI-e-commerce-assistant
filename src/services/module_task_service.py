"""V11.8 role-scoped task lifecycle service.

New tasks must arrive as structured SOP task packages. The legacy rule chain may
read historical tasks, but it cannot generate new tasks anymore.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Callable, Dict, List
from uuid import uuid4

from src.services.account_service import default_reviewer, get_user, user_display

PRIORITY_RANK = {"高": 1, "中": 2, "低": 3}
DONE_STATUS = {"已完成", "已拒绝", "已确认", "已归档", "已通过", "已写入复盘"}
FINANCE_DOMAINS = {"报表", "价格", "流量", "库存", "利润", "财务"}
EVENT_LABELS = {
    "task_created": "任务创建",
    "task_merged": "任务合并",
    "task_updated": "任务更新",
    "manager_split": "总管拆分",
    "manager_assigned": "总管派发",
    "operator_accepted": "运营接收",
    "operator_submitted": "运营提交",
    "manager_approved": "复核通过",
    "manager_returned": "复核退回",
    "task_completed": "任务完成",
    "task_written_to_recap": "写入复盘",
    "task_pinned": "任务置顶",
    "task_reordered": "任务排序",
    "demo_reset": "演示重置",
}
REQUIRED_V118_FIELDS = {"taskCard", "taskDetailReport", "evidencePack", "sopSteps", "reviewMetrics", "completionGate", "failureThreshold", "agentJudgment", "ownership"}

TASKS: List[Dict[str, Any]] = []
LOGS: List[Dict[str, Any]] = []
TASK_EVENTS: List[Dict[str, Any]] = []


def now_time() -> str:
    return datetime.now().strftime("%H:%M")


def now_iso() -> str:
    return datetime.now().isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}{uuid4().hex[:10]}".upper()


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def validate_v118_task_package(payload: Dict[str, Any]) -> None:
    if payload.get("taskGenerationMode") != "v11_8_sop_package":
        raise ValueError("旧任务生成规则已删除：新任务必须由 V11.8 SOP 任务包生成。")
    missing = sorted(field for field in REQUIRED_V118_FIELDS if field not in payload)
    if missing:
        raise ValueError(f"任务结构缺失：{', '.join(missing)}。请从经营对象 + 指标证据 + SOP 链路重新生成任务。")
    if (payload.get("agentJudgment") or {}).get("status") in {"v5_rule_based", "rule_based", "legacy"}:
        raise ValueError("旧 agentJudgment 已禁止生成新任务。")


def build_dedupe_key(task: Dict[str, Any]) -> str:
    ownership = task.get("ownership") or {}
    entity_type = task.get("entityType") or "商品"
    entity_id = task.get("entityId") or task.get("productId") or task.get("id") or "unknown"
    risk_domain = task.get("riskDomain") or (task.get("taskCard") or {}).get("subtitle") or "经营"
    action_type = task.get("actionType") or "SOP"
    owner = ownership.get("assignedOperatorId") or ownership.get("ownerUserId") or "global"
    source_event = task.get("sourceEvent") or ""
    return f"{owner}:{entity_type}:{entity_id}:{risk_domain}:{action_type}:{source_event}"


def normalize_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """Only normalize lifecycle fields; never infer business meaning."""
    validate_v118_task_package(task)
    item = deepcopy(task)
    ownership = item.get("ownership") or {}
    card = item.get("taskCard") or {}
    item.setdefault("id", make_id("A"))
    item.setdefault("priority", card.get("priority") or "中")
    item.setdefault("priorityLevel", "danger" if item["priority"] == "高" else "good" if item["priority"] == "低" else "warning")
    item.setdefault("deadline", card.get("deadline") or "本周内")
    item.setdefault("timeBucket", item.get("deadline", "本周内"))
    item.setdefault("title", card.get("title") or item.get("productId") or "经营任务")
    item.setdefault("productTitle", item.get("title"))
    item.setdefault("productShort", item.get("productId") or item.get("entityId") or "任务")
    item.setdefault("source", item.get("sourceModule") or "SOP任务包")
    item.setdefault("sourceModule", item.get("source") or "SOP任务包")
    item.setdefault("sourceRoute", "business-actions")
    item.setdefault("productRoute", item.get("sourceRoute") or "business-products")
    item.setdefault("todoRoute", "business-actions")
    item.setdefault("logRoute", "business-report")
    item.setdefault("entityType", "商品")
    item.setdefault("entityId", item.get("productId") or item.get("id"))
    item.setdefault("taskLayer", "manager_dispatch" if item.get("priority") == "高" else "operator_execution")
    item.setdefault("assigneeId", ownership.get("assignedOperatorId") if item.get("taskLayer") == "operator_execution" else None)
    item.setdefault("reviewerId", ownership.get("reviewerId") or (default_reviewer() or {}).get("id"))
    item.setdefault("visibleUserIds", ownership.get("visibleUserIds") or [])
    item.setdefault("visibleRoleIds", ownership.get("visibleRoleIds") or ["owner", "manager", "operator"])
    if item.get("assigneeId") and item["assigneeId"] not in item["visibleUserIds"]:
        item["visibleUserIds"].append(item["assigneeId"])
    if item.get("reviewerId") and item["reviewerId"] not in item["visibleUserIds"]:
        item["visibleUserIds"].append(item["reviewerId"])
    item.setdefault("visibleStoreIds", item.get("storeIds") or [])
    item.setdefault("createdByRole", "system")
    item.setdefault("parentTaskId", None)
    item.setdefault("childTaskIds", [])
    item.setdefault("recapTarget", "日报" if item["taskLayer"] == "operator_execution" else "周报")
    item.setdefault("createdAt", now_iso())
    item.setdefault("updatedAt", item["createdAt"])
    item.setdefault("manualOrder", int(datetime.now().timestamp() * 1000))
    item.setdefault("status", "待拆分" if item["taskLayer"] == "manager_dispatch" else "待接收")
    item.setdefault("workflowStatus", "待拆分" if item["taskLayer"] == "manager_dispatch" else "待接收")
    item["assigneeName"] = user_display(item.get("assigneeId"), "未派发")
    item["reviewerName"] = user_display(item.get("reviewerId"), "未设置复核人")
    item.setdefault("assignedById", None)
    item["assignedByName"] = user_display(item.get("assignedById"), "系统预警" if item.get("assigneeId") else "未下发")
    item["dedupeKey"] = item.get("dedupeKey") or build_dedupe_key(item)
    item["sourceTrail"] = list(dict.fromkeys(value for value in [*(item.get("sourceTrail") or []), item.get("sourceModule"), "V11.8 SOP任务包"] if value))
    return item


def user_store_overlap(task: Dict[str, Any], user: Dict[str, Any]) -> bool:
    task_store_ids = set(task.get("visibleStoreIds") or task.get("storeIds") or [])
    user_store_ids = set(user.get("storeIds") or [])
    return bool(task_store_ids and user_store_ids and task_store_ids & user_store_ids)


def task_visible_to_viewer(task: Dict[str, Any], viewer_id: str | None = None) -> bool:
    user = get_user(viewer_id)
    if not user:
        return True
    role_id = user.get("roleId")
    role_visible = role_id in set(task.get("visibleRoleIds") or [])
    user_visible = user.get("id") in set(task.get("visibleUserIds") or [])
    if role_id in {"owner", "manager", "finance"}:
        return role_visible or True
    if role_id == "operator":
        return user_visible or (task.get("taskLayer") == "operator_execution" and user_store_overlap(task, user))
    if role_id == "observer":
        return task.get("status") in DONE_STATUS or role_visible
    return False


def available_actions_for_viewer(task: Dict[str, Any], viewer_id: str | None = None) -> List[str]:
    user = get_user(viewer_id)
    if not user:
        return ["report", "assign", "accept", "submit", "review", "write_recap", "pin", "move", "source"]
    role_id = user.get("roleId")
    status = task.get("status")
    if role_id == "owner":
        return ["report", "source"]
    if role_id == "manager":
        actions = ["report", "source", "pin", "move", "assign"]
        if status in {"已提交", "待复核"}:
            actions.append("review")
        if status in {"已完成", "已通过", "已归档"}:
            actions.append("write_recap")
        return actions
    if role_id in {"operator", "finance"}:
        actions = ["report", "source"]
        if status in {"待接收", "待确认", "已派发"}:
            actions.append("accept")
        if status in {"处理中", "已退回"} or task.get("workflowStatus") == "已退回":
            actions.append("submit")
        return actions
    return ["report", "source"]


def project_task_for_viewer(task: Dict[str, Any], viewer_id: str | None = None) -> Dict[str, Any]:
    item = deepcopy(task)
    user = get_user(viewer_id)
    item["availableActions"] = available_actions_for_viewer(item, viewer_id)
    if user:
        item["viewerRoleId"] = user.get("roleId")
        item["viewerRoleName"] = user.get("roleName")
        item["viewerInsightDepth"] = user.get("insightDepth")
    item["recentEvents"] = [event for event in TASK_EVENTS if event.get("taskId") == item.get("id")][:5]
    return item


def sort_tasks(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(tasks, key=lambda task: (PRIORITY_RANK.get(task.get("priority"), 9), task.get("manualOrder", 9999), task.get("createdAt", "")))


def create_task_event(task: Dict[str, Any], event_type: str, actor_user_id: str | None = None, from_status: str | None = None, from_workflow: str | None = None, message: str | None = None, target_user_ids: List[str] | None = None, target_role_ids: List[str] | None = None) -> Dict[str, Any]:
    actor = get_user(actor_user_id) if actor_user_id and actor_user_id != "system" else None
    event = {
        "id": make_id("E"),
        "taskId": task.get("id"),
        "eventType": event_type,
        "eventLabel": EVENT_LABELS.get(event_type, event_type),
        "actorUserId": actor_user_id or "system",
        "actorRole": actor.get("roleId") if actor else "system",
        "actorName": actor.get("name") if actor else "系统",
        "fromStatus": from_status,
        "toStatus": task.get("status"),
        "fromWorkflowStatus": from_workflow,
        "toWorkflowStatus": task.get("workflowStatus"),
        "targetUserIds": list(dict.fromkeys(target_user_ids if target_user_ids is not None else task.get("visibleUserIds", []))),
        "targetRoleIds": list(dict.fromkeys(target_role_ids if target_role_ids is not None else task.get("visibleRoleIds", []))),
        "message": message or EVENT_LABELS.get(event_type, "任务已更新"),
        "createdAt": now_iso(),
    }
    TASK_EVENTS.insert(0, event)
    del TASK_EVENTS[300:]
    task["lastEventType"] = event_type
    task["lastEventMessage"] = event["message"]
    task["lastEventAt"] = event["createdAt"]
    return deepcopy(event)


def create_log(payload: Dict[str, Any]) -> Dict[str, Any]:
    task = payload.get("task") or {}
    card = task.get("taskCard") or {}
    log = {
        "id": payload.get("id") or make_id("G"),
        "time": payload.get("time") or now_time(),
        "type": payload.get("type") or "任务记录",
        "source": payload.get("source") or task.get("source") or task.get("sourceModule") or "系统",
        "status": payload.get("status") or task.get("status") or "已记录",
        "level": payload.get("level") or task.get("priorityLevel") or "good",
        "imageLabel": payload.get("imageLabel") or task.get("imageLabel") or "记",
        "title": payload.get("title") or card.get("title") or task.get("title") or "任务记录",
        "platform": payload.get("platform") or task.get("platform") or "经营单元",
        "store": payload.get("store") or task.get("store") or "任务池",
        "productId": payload.get("productId") or task.get("productId") or task.get("id") or "TASK",
        "action": payload.get("action") or "任务池动作",
        "reason": payload.get("reason") or (task.get("taskDetailReport") or {}).get("warningSummary") or task.get("reason") or "来自 V11.8 SOP 任务包。",
        "result": payload.get("result") or "已写入日志。",
        "route": payload.get("route") or task.get("sourceRoute") or "dashboard",
        "taskRoute": payload.get("taskRoute") or "business-actions",
        "operator": payload.get("operator") or task.get("assigneeName") or task.get("assignedByName") or "系统",
        "createdAt": now_iso(),
    }
    LOGS.insert(0, log)
    del LOGS[200:]
    return deepcopy(log)


def event_visible_to_user(event: Dict[str, Any], user_id: str | None = None) -> bool:
    user = get_user(user_id)
    if not user:
        return True
    if event.get("actorUserId") == user.get("id"):
        return True
    if user.get("id") in set(event.get("targetUserIds") or []):
        return True
    if user.get("roleId") in set(event.get("targetRoleIds") or []):
        task = find_task(event.get("taskId"))
        return True if not task else task_visible_to_viewer(task, user_id)
    return False


def list_task_events_for_user(viewer_id: str | None = None, limit: int = 30) -> List[Dict[str, Any]]:
    return [deepcopy(event) for event in TASK_EVENTS if event_visible_to_user(event, viewer_id)][:limit]


def list_tasks(active_only: bool = False, assignee_id: str | None = None, review_scope: bool = False, viewer_id: str | None = None) -> List[Dict[str, Any]]:
    tasks = [task for task in TASKS if not active_only or task.get("status") not in DONE_STATUS]
    if assignee_id:
        tasks = [task for task in tasks if task.get("assigneeId") == assignee_id]
    if review_scope:
        tasks = [task for task in tasks if task.get("status") == "待复核"]
    if viewer_id:
        tasks = [task for task in tasks if task_visible_to_viewer(task, viewer_id)]
    return [project_task_for_viewer(task, viewer_id) for task in sort_tasks(tasks)]


def get_task_counters_for_user(viewer_id: str | None = None) -> Dict[str, Any]:
    visible = list_tasks(active_only=True, viewer_id=viewer_id)
    events = list_task_events_for_user(viewer_id, limit=30)
    return {
        "visibleActive": len(visible),
        "waitingAccept": len([task for task in visible if task.get("status") in {"待接收", "待确认"}]),
        "processing": len([task for task in visible if task.get("status") == "处理中"]),
        "submitted": len([task for task in visible if task.get("status") in {"已提交", "待复核"}]),
        "reviewing": len([task for task in visible if task.get("status") == "待复核"]),
        "returned": len([task for task in visible if task.get("workflowStatus") == "已退回"]),
        "waitingRecap": len([task for task in visible if task.get("status") == "已完成" and task.get("recapTarget") in {"日报", "周报", "月报"}]),
        "recentEvents": len(events),
        "latestEvent": events[0] if events else None,
    }


def list_logs() -> List[Dict[str, Any]]:
    return deepcopy(LOGS)


def find_task(task_id: str | None) -> Dict[str, Any] | None:
    return next((item for item in TASKS if item.get("id") == task_id), None)


def find_task_by_key(dedupe_key: str, *, active_only: bool = False, done_only: bool = False) -> Dict[str, Any] | None:
    for task in TASKS:
        if task.get("dedupeKey") != dedupe_key:
            continue
        is_done = task.get("status") in DONE_STATUS
        if active_only and is_done:
            continue
        if done_only and not is_done:
            continue
        return task
    return None


def find_open_task_by_key(dedupe_key: str) -> Dict[str, Any] | None:
    return find_task_by_key(dedupe_key, active_only=True)


def find_completed_task_by_key(dedupe_key: str) -> Dict[str, Any] | None:
    return find_task_by_key(dedupe_key, done_only=True)


def task_state_for_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        suggested_key = build_dedupe_key(payload)
    except Exception:
        suggested_key = "legacy-disabled"
    active = find_open_task_by_key(suggested_key)
    completed = find_completed_task_by_key(suggested_key)
    archived = bool(completed and not active)
    return {"suggestedTaskKey": suggested_key, "activeTaskId": active.get("id") if active else None, "activeTaskStatus": active.get("status") if active else None, "activeWorkflowStatus": active.get("workflowStatus") if active else None, "activeAssigneeName": active.get("assigneeName") if active else None, "completedTaskId": completed.get("id") if completed else None, "completedTaskStatus": completed.get("status") if completed else None, "hasActiveTask": bool(active), "candidateArchived": archived, "candidateStatus": "completed_archived" if archived else "active_task" if active else "pending_candidate"}


def attach_task_state(item: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    result = deepcopy(item)
    result.update(task_state_for_payload(payload))
    return result


def visible_candidates(items: List[Dict[str, Any]], payload_builder: Callable[[Dict[str, Any]], Dict[str, Any]]) -> List[Dict[str, Any]]:
    visible: List[Dict[str, Any]] = []
    for item in items:
        try:
            payload = payload_builder(item)
            annotated = attach_task_state(item, payload)
        except Exception:
            annotated = deepcopy(item)
            annotated["legacyTaskCreationDisabled"] = True
            annotated["candidateStatus"] = "object_only"
        if annotated.get("candidateArchived"):
            continue
        visible.append(annotated)
    return visible


def create_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    task = normalize_task(payload)
    existing = find_open_task_by_key(task["dedupeKey"])
    if existing:
        existing.update({"updatedAt": now_iso(), "dedupeHit": True})
        create_task_event(existing, "task_merged", message="相同来源 SOP 任务已合并。")
        return deepcopy(existing)
    TASKS.insert(0, task)
    create_task_event(task, "task_created", message="任务已由 V11.8 SOP 任务包生成。")
    create_log({"type": "任务进入池", "task": task, "status": "已加入任务池", "action": "生成SOP任务", "result": "任务已按经营对象归属同步到相关账号。"})
    return deepcopy(task)


def create_task_from_warning(payload: Dict[str, Any]) -> Dict[str, Any]:
    return create_task(payload)


def create_task_from_review_audit(payload: Dict[str, Any]) -> Dict[str, Any]:
    return create_task(payload)


def update_task(task_id: str, patch: Dict[str, Any], *, log_type: str | None = None, action: str | None = None, result: str | None = None) -> Dict[str, Any] | None:
    task = find_task(task_id)
    if not task:
        return None
    before_status = task.get("status")
    before_workflow = task.get("workflowStatus")
    task.update(deepcopy(patch))
    task["updatedAt"] = now_iso()
    task["assigneeName"] = user_display(task.get("assigneeId"), "未派发")
    task["reviewerName"] = user_display(task.get("reviewerId"), "未设置复核人")
    if log_type:
        create_log({"type": log_type, "task": task, "action": action or log_type, "result": result or "任务已更新。"})
    create_task_event(task, "task_completed" if task.get("status") in DONE_STATUS and before_status != task.get("status") else "task_updated", from_status=before_status, from_workflow=before_workflow, message=result or "任务已更新。")
    return deepcopy(task)


def submit_task(task_id: str, note: str | None = None, submitter_id: str | None = None) -> Dict[str, Any] | None:
    """Lifecycle-only submit adapter used by evidence forms."""
    return update_task(
        task_id,
        {"status": "待复核", "workflowStatus": "待复核", "submissionNote": note or "运营已提交处理结果。", "submittedById": submitter_id, "submittedAt": now_iso()},
        log_type="任务提交",
        action="提交复核",
        result=note or "运营已提交处理结果，等待复核。",
    )


def review_task(task_id: str, decision: str = "approve", note: str | None = None, reviewer_id: str | None = None) -> Dict[str, Any] | None:
    """Lifecycle-only review adapter used by evidence review."""
    approved = decision in {"approve", "approved", "pass", "通过"}
    return update_task(
        task_id,
        {
            "status": "已完成" if approved else "已退回",
            "workflowStatus": "已通过" if approved else "已退回",
            "reviewResult": "通过" if approved else "退回",
            "reviewNote": note or ("复核通过。" if approved else "复核退回。"),
            "reviewerId": reviewer_id,
            "reviewedAt": now_iso(),
        },
        log_type="任务复核",
        action="复核通过" if approved else "复核退回",
        result=note or ("复核通过。" if approved else "复核退回。"),
    )


def pin_task(task_id: str) -> Dict[str, Any] | None:
    """Lifecycle-only pin adapter kept for the todo route."""
    task = find_task(task_id)
    if not task:
        return None
    task["manualOrder"] = 0
    task["pinned"] = True
    task["updatedAt"] = now_iso()
    create_task_event(task, "task_pinned", message="任务已置顶。")
    return deepcopy(task)


def reorder_task(task_id: str, direction: str = "down") -> Dict[str, Any] | None:
    """Lifecycle-only reorder adapter kept for the todo route."""
    ordered = sort_tasks(TASKS)
    index = next((i for i, item in enumerate(ordered) if item.get("id") == task_id), None)
    if index is None:
        return None
    target_index = index - 1 if direction in {"up", "top", "prev", "上移"} else index + 1
    if target_index < 0 or target_index >= len(ordered):
        return deepcopy(ordered[index])
    current = ordered[index]
    target = ordered[target_index]
    current_order = current.get("manualOrder", index)
    target_order = target.get("manualOrder", target_index)
    current["manualOrder"], target["manualOrder"] = target_order, current_order
    current["updatedAt"] = now_iso()
    target["updatedAt"] = now_iso()
    create_task_event(current, "task_reordered", message="任务排序已更新。")
    return deepcopy(current)
