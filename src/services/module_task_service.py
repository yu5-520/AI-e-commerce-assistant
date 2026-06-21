"""V5 role-scoped task flow service.

The product runtime starts with no business tasks. Tasks are created only from
imported data, module candidates, manager dispatch, or explicit user actions.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Callable, Dict, List
from uuid import uuid4

from src.services.account_service import default_operator, default_reviewer, get_user, list_stores, users_by_role, user_display

PRIORITY_RANK = {"高": 1, "中": 2, "低": 3}
DONE_STATUS = {"已完成", "已拒绝", "已确认", "已归档", "已通过", "已写入复盘"}
FINANCE_DOMAINS = {"报表", "价格", "流量", "库存", "利润", "财务"}
EVENT_LABELS = {
    "task_created": "任务创建",
    "task_merged": "任务合并",
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

TASKS: List[Dict[str, Any]] = []
LOGS: List[Dict[str, Any]] = []
TASK_EVENTS: List[Dict[str, Any]] = []


def now_time() -> str:
    return datetime.now().strftime("%H:%M")


def now_iso() -> str:
    return datetime.now().isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}{uuid4().hex[:10]}".upper()


def store_id_map() -> Dict[str, Dict[str, Any]]:
    return {store["id"]: store for store in list_stores()}


def store_name_map() -> Dict[str, Dict[str, Any]]:
    mapping: Dict[str, Dict[str, Any]] = {}
    for store in list_stores():
        mapping[store["name"]] = store
        mapping[f"{store['platform']} · {store['name']}"] = store
        mapping[store["platform"]] = store
    return mapping


def infer_store_ids(task: Dict[str, Any]) -> List[str]:
    explicit = task.get("storeIds") or task.get("visibleStoreIds")
    if isinstance(explicit, list) and explicit:
        return list(dict.fromkeys(explicit))
    mapping = store_name_map()
    ids: List[str] = []
    for value in [task.get("store"), task.get("storeName"), task.get("platform")]:
        if value and value in mapping:
            ids.append(mapping[value]["id"])
    return list(dict.fromkeys(ids))


def infer_store_group_id(store_ids: List[str]) -> str | None:
    stores = store_id_map()
    for store_id in store_ids:
        group_id = stores.get(store_id, {}).get("groupId")
        if group_id:
            return group_id
    return None


def operator_for_store(store_ids: List[str], risk_domain: str | None = None) -> Dict[str, Any] | None:
    for user in users_by_role("operator"):
        if set(user.get("storeIds") or []) & set(store_ids):
            return user
    return default_operator(risk_domain) if users_by_role("operator") else None


def finance_user() -> Dict[str, Any] | None:
    users = users_by_role("finance")
    return users[0] if users else None


def infer_domain(task: Dict[str, Any]) -> str:
    text = " ".join(str(item) for item in [task.get("riskDomain"), task.get("taskType"), task.get("taskSignal"), task.get("task"), task.get("reason"), *(task.get("judgmentTags") or [])] if item)
    if any(word in text for word in ["售后", "退款", "尺寸", "材质", "安装", "客服"]):
        return "售后"
    if any(word in text for word in ["库存", "补货", "承接"]):
        return "库存"
    if any(word in text for word in ["流量", "ROI", "推广", "投放", "点击", "转化", "ROAS"]):
        return "流量"
    if any(word in text for word in ["上新", "主图", "标题", "SKU", "详情页", "测试版本"]):
        return "上新"
    if any(word in text for word in ["价格", "利润", "券", "活动价", "财务"]):
        return "价格"
    if any(word in text for word in ["报表", "导入", "同步", "数据"]):
        return "报表"
    return "通用"


def infer_action(task: Dict[str, Any]) -> str:
    text = " ".join(str(item) for item in [task.get("actionType"), task.get("taskType"), task.get("taskSignal"), task.get("task")] if item)
    if "复盘" in text:
        return "复盘"
    if any(word in text for word in ["测试", "版本", "上新"]):
        return "测试"
    if any(word in text for word in ["导入", "同步"]):
        return "导入"
    if "观察" in text:
        return "观察"
    if "确认" in text:
        return "确认"
    return "复查"


def infer_source_type(task: Dict[str, Any]) -> str:
    route = task.get("sourceRoute") or ""
    source = f"{task.get('source') or ''} {task.get('sourceModule') or ''}"
    if route == "business-products" or "商品" in source:
        return "商品模块"
    if route == "business-competitors" or "竞品" in source:
        return "竞品模块"
    if route == "business-listing" or "上新" in source:
        return "上新模块"
    if route == "business-traffic" or "流量" in source:
        return "流量模块"
    if route == "data-check" or "报表" in source:
        return "财务报表"
    if "系统" in source or "预警" in source:
        return "系统预警"
    if any(word in source for word in ["复盘", "周报", "月报", "日报", "审计"]):
        return "复盘审计"
    return "手动创建"


def infer_task_layer(task: Dict[str, Any], source_type: str, risk_domain: str) -> str:
    if task.get("taskLayer"):
        return str(task["taskLayer"])
    if source_type in {"复盘审计"}:
        return "manager_dispatch"
    if source_type == "财务报表" or risk_domain in FINANCE_DOMAINS:
        return "finance_check"
    return "operator_execution"


def default_visible_roles(layer: str, risk_domain: str) -> List[str]:
    if layer == "owner_decision":
        return ["owner"]
    if layer == "manager_dispatch":
        return ["manager"]
    if layer == "finance_check":
        return ["manager", "finance"]
    roles = ["manager", "operator"]
    if risk_domain in FINANCE_DOMAINS:
        roles.append("finance")
    return roles


def build_dedupe_key(task: Dict[str, Any]) -> str:
    entity_type = task.get("entityType") or ("报表" if str(task.get("productId", "")).startswith("R") else "商品")
    entity_id = task.get("entityId") or task.get("productId") or task.get("sourceEvent") or task.get("id") or "unknown"
    risk_domain = task.get("riskDomain") or infer_domain(task)
    action_type = task.get("actionType") or infer_action(task)
    store_ids = "+".join(task.get("storeIds") or infer_store_ids(task) or ["global"])
    source_event = task.get("sourceEvent") or ""
    return f"{store_ids}:{entity_type}:{entity_id}:{risk_domain}:{action_type}:{source_event}"


def normalize_task(task: Dict[str, Any]) -> Dict[str, Any]:
    item = deepcopy(task)
    item.setdefault("id", make_id("A"))
    item.setdefault("priority", "中")
    item.setdefault("priorityLevel", "danger" if item["priority"] == "高" else "good" if item["priority"] == "低" else "warning")
    item.setdefault("deadline", "本周内")
    item.setdefault("timeBucket", item.get("deadline", "本周内"))
    item.setdefault("source", item.get("sourceModule") or "系统")
    item.setdefault("sourceModule", item.get("source") or "系统")
    item.setdefault("sourceRoute", "dashboard")
    item.setdefault("productRoute", item.get("sourceRoute") or "business-products")
    item.setdefault("todoRoute", "business-actions")
    item.setdefault("logRoute", "business-report")
    item.setdefault("entityType", "报表" if str(item.get("productId", "")).startswith("R") else "商品")
    item.setdefault("entityId", item.get("productId") or item.get("id"))
    item.setdefault("riskDomain", infer_domain(item))
    item.setdefault("actionType", infer_action(item))
    item.setdefault("sourceType", infer_source_type(item))
    item.setdefault("storeIds", infer_store_ids(item))
    item.setdefault("storeGroupId", infer_store_group_id(item.get("storeIds") or []))
    item.setdefault("taskLayer", infer_task_layer(item, item["sourceType"], item["riskDomain"]))
    item.setdefault("createdByRole", "system")
    item.setdefault("parentTaskId", None)
    item.setdefault("childTaskIds", [])
    item.setdefault("recapTarget", "日报" if item["taskLayer"] == "operator_execution" else "周报")
    item.setdefault("agentJudgment", {"status": "v5_rule_based", "summary": "任务由导入数据、模块归属和账号权限生成。"})
    item.setdefault("evidence", [])
    item.setdefault("judgmentTags", [])
    item.setdefault("sourceTrail", [])
    item.setdefault("createdAt", now_iso())
    item.setdefault("updatedAt", item["createdAt"])
    item.setdefault("manualOrder", int(datetime.now().timestamp() * 1000))
    item.setdefault("title", item.get("productTitle") or item.get("task") or item.get("taskType") or "经营任务")
    item.setdefault("productTitle", item.get("title"))
    item.setdefault("productShort", item.get("shortName") or item.get("productId") or "任务")

    if item["taskLayer"] == "operator_execution" and not item.get("assigneeId"):
        operator = operator_for_store(item.get("storeIds") or [], item.get("riskDomain"))
        if operator:
            item["assigneeId"] = operator["id"]
            item.setdefault("workflowStatus", "已派发")
            item.setdefault("status", "待接收")
    elif item["taskLayer"] == "finance_check" and not item.get("assigneeId"):
        finance = finance_user()
        if finance:
            item["assigneeId"] = finance["id"]
            item.setdefault("workflowStatus", "已派发")
            item.setdefault("status", "待接收")
    else:
        item.setdefault("assigneeId", None)

    item.setdefault("status", "待拆分" if item["taskLayer"] == "manager_dispatch" else "待接收")
    item.setdefault("workflowStatus", "待拆分" if item["taskLayer"] == "manager_dispatch" else "待接收")
    item.setdefault("reviewerId", default_reviewer()["id"] if item["taskLayer"] in {"operator_execution", "finance_check"} else None)
    item["assigneeName"] = user_display(item.get("assigneeId"), "未派发")
    item["reviewerName"] = user_display(item.get("reviewerId"), "未设置复核人")
    item.setdefault("assignedById", None)
    item["assignedByName"] = user_display(item.get("assignedById"), "系统预警" if item.get("assigneeId") else "未下发")
    item.setdefault("visibleRoleIds", default_visible_roles(item["taskLayer"], item["riskDomain"]))
    visible_users = set(item.get("visibleUserIds") or [])
    if item.get("assigneeId"):
        visible_users.add(item["assigneeId"])
    if item.get("reviewerId"):
        visible_users.add(item["reviewerId"])
    item["visibleUserIds"] = list(visible_users)
    item.setdefault("visibleStoreIds", item.get("storeIds") or [])
    item["dedupeKey"] = item.get("dedupeKey") or build_dedupe_key(item)
    item["sourceTrail"] = list(dict.fromkeys(value for value in [*(item.get("sourceTrail") or []), item.get("sourceModule")] if value))
    return item


def user_store_overlap(task: Dict[str, Any], user: Dict[str, Any]) -> bool:
    task_store_ids = set(task.get("visibleStoreIds") or task.get("storeIds") or [])
    user_store_ids = set(user.get("storeIds") or [])
    return bool(task_store_ids and user_store_ids and task_store_ids & user_store_ids)


def task_group_visible(task: Dict[str, Any], user: Dict[str, Any]) -> bool:
    if task.get("storeGroupId") and task.get("storeGroupId") in set(user.get("storeGroupIds") or []):
        return True
    return user_store_overlap(task, user)


def task_visible_to_viewer(task: Dict[str, Any], viewer_id: str | None = None) -> bool:
    user = get_user(viewer_id)
    if not user:
        return True
    role_id = user.get("roleId")
    role_visible = role_id in set(task.get("visibleRoleIds") or [])
    user_visible = user.get("id") in set(task.get("visibleUserIds") or [])
    if role_id == "owner":
        return role_visible or task.get("taskLayer") in {"owner_decision", "review_audit", "cycle_draft"}
    if role_id == "manager":
        return role_visible and task_group_visible(task, user)
    if role_id == "operator":
        return user_visible or (task.get("taskLayer") == "operator_execution" and user_store_overlap(task, user))
    if role_id == "finance":
        return user_visible or role_visible or task.get("riskDomain") in FINANCE_DOMAINS
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
    log = {
        "id": payload.get("id") or make_id("G"),
        "time": payload.get("time") or now_time(),
        "type": payload.get("type") or "任务记录",
        "source": payload.get("source") or task.get("source") or task.get("sourceModule") or "系统",
        "status": payload.get("status") or task.get("status") or "已记录",
        "level": payload.get("level") or task.get("priorityLevel") or "good",
        "imageLabel": payload.get("imageLabel") or task.get("imageLabel") or "记",
        "title": payload.get("title") or task.get("title") or task.get("productTitle") or "任务记录",
        "platform": payload.get("platform") or task.get("platform") or "经营单元",
        "store": payload.get("store") or task.get("store") or "任务池",
        "productId": payload.get("productId") or task.get("productId") or task.get("id") or "TASK",
        "action": payload.get("action") or "任务池动作",
        "reason": payload.get("reason") or task.get("reason") or "来自统一任务池。",
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
    suggested_key = build_dedupe_key(payload)
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
        annotated = attach_task_state(item, payload_builder(item))
        if annotated.get("candidateArchived"):
            continue
        visible.append(annotated)
    return visible


def create_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    task = normalize_task(payload)
    existing = find_open_task_by_key(task["dedupeKey"])
    if existing:
        existing.update({"updatedAt": now_iso(), "dedupeHit": True})
        create_task_event(existing, "task_merged", message="相同来源任务已合并。")
        return deepcopy(existing)
    TASKS.insert(0, task)
    create_task_event(task, "task_created", message="任务已按数据、模块和账号权限生成。")
    create_log({"type": "任务进入池", "task": task, "status": "已加入任务池", "action": "生成任务", "result": "任务已同步到相关账号。"})
    return deepcopy(task)


def create_task_from_warning(payload: Dict[str, Any]) -> Dict[str, Any]:
    task = dict(payload)
    task.setdefault("sourceType", infer_source_type(task))
    task.setdefault("taskLayer", "finance_check" if task.get("riskDomain") in FINANCE_DOMAINS or task.get("sourceRoute") == "data-check" else "operator_execution")
    return create_task(task)


def create_task_from_review_audit(payload: Dict[str, Any]) -> Dict[str, Any]:
    task = dict(payload)
    task.setdefault("sourceType", "复盘审计")
    task.setdefault("taskLayer", "manager_dispatch")
    task.setdefault("status", "待拆分")
    task.setdefault("workflowStatus", "待拆分")
    task.setdefault("visibleRoleIds", ["manager"])
    return create_task(task)


def update_task(task_id: str, patch: Dict[str, Any], *, log_type: str | None = None, action: str | None = None, result: str | None = None) -> Dict[str, Any] | None:
    task = find_task(task_id)
    if not task:
        return None
    task.update(deepcopy(patch))
    task["updatedAt"] = now_iso()
    task["assigneeName"] = user_display(task.get("assigneeId"), "未派发")
    task["reviewerName"] = user_display(task.get("reviewerId"), "未设置复核人")
    if log_type:
        create_log({"type": log_type, "task": task, "action": action or log_type, "result": result or "任务已更新。"})
    return deepcopy(task)


def transition_task(task_id: str, action: str, actor_user_id: str | None = None, payload: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
    payload = payload or {}
    task = find_task(task_id)
    if not task:
        return None
    from_status = task.get("status")
    from_workflow = task.get("workflowStatus")
    if action == "manager_assigned":
        task["assigneeId"] = payload.get("assignee_id") or payload.get("assigneeId") or task.get("assigneeId")
        task["reviewerId"] = payload.get("reviewer_id") or payload.get("reviewerId") or task.get("reviewerId") or default_reviewer()["id"]
        task["status"] = "待接收"
        task["workflowStatus"] = "已派发"
        task["assignmentNote"] = payload.get("note") or ""
    elif action == "manager_split":
        task["status"] = "待接收"
        task["workflowStatus"] = "已拆分"
    elif action == "operator_accepted":
        task["status"] = "处理中"
        task["workflowStatus"] = "处理中"
        task["acceptedAt"] = now_iso()
    elif action == "operator_submitted":
        task["status"] = "待复核"
        task["workflowStatus"] = "待复核"
        task["submissionNote"] = payload.get("note") or payload.get("submissionNote") or ""
        task["submittedAt"] = now_iso()
    elif action == "manager_returned":
        task["status"] = "已退回"
        task["workflowStatus"] = "已退回"
        task["reviewNote"] = payload.get("note") or ""
    elif action == "manager_approved":
        task["status"] = "已完成"
        task["workflowStatus"] = "复核通过"
        task["reviewNote"] = payload.get("note") or ""
        task["reviewedAt"] = now_iso()
    elif action == "task_completed":
        task["status"] = "已完成"
        task["workflowStatus"] = "已完成"
    elif action == "task_written_to_recap":
        task["status"] = "已写入复盘"
        task["workflowStatus"] = "已写入复盘"
        task["recapTarget"] = payload.get("recapTarget") or payload.get("recap_target") or task.get("recapTarget")
        task["recapWrittenAt"] = now_iso()
    task["updatedAt"] = now_iso()
    task["assigneeName"] = user_display(task.get("assigneeId"), "未派发")
    task["reviewerName"] = user_display(task.get("reviewerId"), "未设置复核人")
    create_task_event(task, action, actor_user_id=actor_user_id, from_status=from_status, from_workflow=from_workflow)
    create_log({"type": EVENT_LABELS.get(action, "任务流转"), "task": task, "action": EVENT_LABELS.get(action, action), "result": "任务状态已同步。"})
    return deepcopy(task)


def split_task_for_operator(task_id: str, operator_id: str | None = None, note: str = "", actor_user_id: str | None = None) -> Dict[str, Any] | None:
    return assign_task(task_id, assignee_id=operator_id, note=note, operator_id=actor_user_id)


def assign_task(task_id: str, assignee_id: str | None = None, reviewer_id: str | None = None, operator_id: str | None = None, note: str = "") -> Dict[str, Any] | None:
    return transition_task(task_id, "manager_assigned", actor_user_id=operator_id, payload={"assigneeId": assignee_id, "reviewerId": reviewer_id, "note": note})


def accept_task(task_id: str, note: str = "", actor_user_id: str | None = None) -> Dict[str, Any] | None:
    return transition_task(task_id, "operator_accepted", actor_user_id=actor_user_id, payload={"note": note})


def submit_task(task_id: str, note: str = "", submitter_id: str | None = None) -> Dict[str, Any] | None:
    return transition_task(task_id, "operator_submitted", actor_user_id=submitter_id, payload={"note": note})


def review_task(task_id: str, decision: str = "approve", note: str = "", reviewer_id: str | None = None) -> Dict[str, Any] | None:
    event = "manager_returned" if decision in {"return", "reject", "rejected", "退回", "拒绝"} else "manager_approved"
    return transition_task(task_id, event, actor_user_id=reviewer_id, payload={"note": note})


def write_task_to_recap(task_id: str, recap_target: str = "日报", note: str = "", actor_user_id: str | None = None) -> Dict[str, Any] | None:
    return transition_task(task_id, "task_written_to_recap", actor_user_id=actor_user_id, payload={"recapTarget": recap_target, "note": note})


def complete_task(task_id: str) -> Dict[str, Any] | None:
    return transition_task(task_id, "task_completed")


def pin_task(task_id: str) -> Dict[str, Any] | None:
    task = find_task(task_id)
    if not task:
        return None
    task["manualOrder"] = 0
    create_task_event(task, "task_pinned")
    return deepcopy(task)


def reorder_task(task_id: str, direction: str = "down") -> Dict[str, Any] | None:
    task = find_task(task_id)
    if not task:
        return None
    delta = 1 if direction == "down" else -1
    task["manualOrder"] = int(task.get("manualOrder", 0)) + delta
    create_task_event(task, "task_reordered")
    return deepcopy(task)


def reset_tasks(viewer_id: str | None = None) -> Dict[str, Any]:
    TASKS.clear()
    LOGS.clear()
    TASK_EVENTS.clear()
    return {"tasks": [], "activeTasks": [], "events": [], "counters": get_task_counters_for_user(viewer_id), "viewerId": viewer_id, "message": "V5 runtime has been reset to empty data state."}
