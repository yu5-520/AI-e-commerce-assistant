"""Role-scoped task flow service for the modular product runtime.

V2.5.0 changes the task system from a single-account todo list into a
role-permission driven task flow:

    warning / review / manual task
    -> role-visible task object
    -> manager split / dispatch
    -> operator submit
    -> manager review
    -> archive / retrospective

The service is still in-memory for the MVP, but every task now carries store
scope, role scope, owner / assignee / reviewer, source type, parent task, and
role-specific actions.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Callable, Dict, List
from uuid import uuid4

from src.services.account_service import (
    default_operator,
    default_reviewer,
    get_user,
    list_stores,
    users_by_role,
    user_display,
)

PRIORITY_RANK = {"高": 1, "中": 2, "低": 3}
DONE_STATUS = {"已完成", "已拒绝", "已确认", "已归档", "已通过"}
OPERATOR_ROUTES = {"business-products", "business-competitors", "business-listing", "business-traffic", "business-actions", "business-report", "operating-unit", "data-check"}
FINANCE_DOMAINS = {"报表", "价格", "流量", "库存", "利润", "财务"}


def now_time() -> str:
    return datetime.now().strftime("%H:%M")


def now_iso() -> str:
    return datetime.now().isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}{uuid4().hex[:10]}".upper()


def store_id_map() -> Dict[str, Dict[str, Any]]:
    return {store["id"]: store for store in list_stores()}


def store_name_map() -> Dict[str, Dict[str, Any]]:
    stores = list_stores()
    mapping: Dict[str, Dict[str, Any]] = {}
    for store in stores:
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
    if "老板" in source or "boss" in source.lower():
        return "老板下发"
    if any(word in source for word in ["复盘", "周报", "月报", "日报", "审计"]):
        return "复盘审计"
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
    return "手动创建"


def infer_task_layer(task: Dict[str, Any], source_type: str, risk_domain: str) -> str:
    if task.get("taskLayer"):
        return str(task["taskLayer"])
    if source_type in {"老板下发", "复盘审计"}:
        return "manager_dispatch"
    if source_type == "财务报表" or risk_domain in FINANCE_DOMAINS:
        return "finance_check"
    if source_type in {"商品模块", "竞品模块", "上新模块", "流量模块", "系统预警"}:
        return "operator_execution"
    return "operator_execution"


def default_visible_roles(layer: str, risk_domain: str) -> List[str]:
    if layer == "owner_decision":
        return ["owner"]
    if layer == "review_audit":
        return ["owner", "manager"]
    if layer == "cycle_draft":
        return ["owner", "manager"]
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
    return f"{store_ids}:{entity_type}:{entity_id}:{risk_domain}:{action_type}"


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
    item.setdefault("ownerRole", "manager" if item["taskLayer"] in {"manager_dispatch", "operator_execution", "finance_check"} else "owner")
    item.setdefault("createdByRole", "system")
    item.setdefault("createdByUserId", None)
    item.setdefault("parentTaskId", None)
    item.setdefault("childTaskIds", [])
    item.setdefault("recapTarget", "日报" if item["taskLayer"] == "operator_execution" else "周报")
    item.setdefault("agentJudgment", {"status": "placeholder", "summary": "后续 Agent 将基于来源报告、ERP / CRM 数据和店铺权限生成判断。"})
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
            item.setdefault("status", "待确认")
    elif item["taskLayer"] == "finance_check" and not item.get("assigneeId"):
        finance = finance_user()
        if finance:
            item["assigneeId"] = finance["id"]
            item.setdefault("workflowStatus", "已派发")
            item.setdefault("status", "待确认")
    else:
        item.setdefault("assigneeId", None)

    item.setdefault("status", "待拆分" if item["taskLayer"] == "manager_dispatch" else "待确认")
    item.setdefault("workflowStatus", "待拆分" if item["taskLayer"] == "manager_dispatch" else "待派发")
    item.setdefault("reviewerId", default_reviewer()["id"] if item["taskLayer"] in {"operator_execution", "finance_check"} else None)
    item["assigneeName"] = user_display(item.get("assigneeId"), "未派发")
    item["reviewerName"] = user_display(item.get("reviewerId"), "未设置复核人")
    item.setdefault("assignedById", None)
    item["assignedByName"] = user_display(item.get("assignedById"), "系统预警" if item.get("assigneeId") else "未下发")
    item.setdefault("assignmentNote", "")
    item.setdefault("submissionNote", "")
    item.setdefault("reviewNote", "")
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


def seed_tasks() -> List[Dict[str, Any]]:
    return [
        normalize_task({"id": "A001", "priority": "高", "priorityLevel": "danger", "deadline": "今天 18:00 前", "source": "流量触发", "sourceModule": "流量测试台", "sourceRoute": "business-traffic", "productId": "P002", "entityType": "商品", "entityId": "P002", "riskDomain": "售后", "actionType": "复查", "imageLabel": "架", "taskType": "售后优先", "taskSignal": "先查售后", "productShort": "厨房置物架", "productTitle": "厨房置物架免打孔收纳架壁挂多层家用置物架", "platform": "拼多多", "store": "家居百货店", "judgmentTags": ["ROI 低", "退款率高", "尺寸咨询高"], "task": "先查售后，不继续放大推广预算", "reason": "搜索推广 ROI 1.1，退款率 6.8%，安装和尺寸咨询偏高。", "manualOrder": 1}),
        normalize_task({"id": "A002", "priority": "高", "priorityLevel": "danger", "deadline": "今天内", "source": "商品触发", "sourceModule": "商品经营列表", "sourceRoute": "business-products", "productId": "P003", "entityType": "商品", "entityId": "P003", "riskDomain": "售后", "actionType": "复查", "imageLabel": "垫", "taskType": "商品复查", "taskSignal": "暂停投放", "productShort": "护腰坐垫", "productTitle": "护腰坐垫久坐办公室靠垫人体工学支撑款", "platform": "抖音小店", "store": "家居好物号", "judgmentTags": ["ROI 低", "退款异常", "售后敏感"], "task": "暂停投放并复查材质、支撑感和客服承诺", "reason": "售后敏感未解决，推荐流量 ROI 0.9，退款率 8.4%。", "manualOrder": 2}),
        normalize_task({"id": "A003", "priority": "中", "priorityLevel": "warning", "deadline": "明天前", "source": "商品触发", "sourceModule": "商品经营列表", "sourceRoute": "business-products", "productId": "P004", "entityType": "商品", "entityId": "P004", "riskDomain": "库存", "actionType": "复查", "imageLabel": "盒", "taskType": "库存承接", "taskSignal": "确认补货周期", "productShort": "收纳盒", "productTitle": "透明收纳盒衣柜整理箱家用大容量防尘款", "platform": "淘宝", "store": "家居生活主店", "judgmentTags": ["库存低", "活动流量"], "task": "确认补货周期，再决定是否继续活动流量", "reason": "库存 46，接近安全线。", "manualOrder": 3}),
        normalize_task({"id": "M001", "priority": "高", "deadline": "下周前", "source": "复盘审计", "sourceModule": "周报复盘", "sourceRoute": "review-audit", "entityType": "复盘", "entityId": "WEEK-001", "riskDomain": "流量", "taskLayer": "manager_dispatch", "taskType": "周期任务草案", "taskSignal": "待拆分", "title": "抖音低 ROAS 商品预算收缩", "productShort": "周报任务", "platform": "抖音小店", "store": "家居好物号", "judgmentTags": ["老板下发", "周报未达标", "需拆分"], "task": "总管拆分给运营 A 和数据财务，形成下周执行任务。", "reason": "周报显示抖音 ROAS 低于目标，需要进入下周任务。", "manualOrder": 0}),
    ]


def seed_logs() -> List[Dict[str, Any]]:
    return [{"id": "G001", "time": "16:08", "type": "任务进入池", "source": "流量触发", "status": "已加入任务池", "level": "danger", "imageLabel": "架", "title": "厨房置物架免打孔收纳架壁挂多层家用置物架", "platform": "拼多多", "store": "家居百货店", "productId": "P002", "action": "搜索推广测试进入统一任务池", "reason": "ROI 1.1，退款率 6.8%。", "result": "进入售后归因，自动分配给负责店铺运营，并同步总管可见。", "route": "business-traffic", "taskRoute": "business-actions", "operator": "系统", "createdAt": now_iso()}]


TASKS: List[Dict[str, Any]] = seed_tasks()
LOGS: List[Dict[str, Any]] = seed_logs()


def sort_tasks(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(tasks, key=lambda task: (PRIORITY_RANK.get(task.get("priority"), 9), task.get("manualOrder", 9999), task.get("createdAt", "")))


def user_store_overlap(task: Dict[str, Any], user: Dict[str, Any]) -> bool:
    task_store_ids = set(task.get("visibleStoreIds") or task.get("storeIds") or [])
    user_store_ids = set(user.get("storeIds") or [])
    return bool(task_store_ids and user_store_ids and task_store_ids & user_store_ids)


def task_group_visible(task: Dict[str, Any], user: Dict[str, Any]) -> bool:
    if task.get("storeGroupId") and task.get("storeGroupId") in set(user.get("storeGroupIds") or []):
        return True
    return user_store_overlap(task, user)


def available_actions_for_viewer(task: Dict[str, Any], viewer_id: str | None = None) -> List[str]:
    user = get_user(viewer_id)
    if not user:
        return ["report", "assign", "submit", "review", "pin", "move", "source"]
    role_id = user.get("roleId")
    if role_id == "owner":
        return ["report", "source"] if task.get("taskLayer") == "operator_execution" else ["report", "source", "review"]
    if role_id == "manager":
        actions = ["report", "source", "pin", "move"]
        if task.get("taskLayer") in {"manager_dispatch", "operator_execution", "finance_check"}:
            actions.insert(1, "assign")
            actions.append("review")
        return actions
    if role_id == "operator":
        actions = ["report", "source"]
        if task.get("assigneeId") == user.get("id") or user_store_overlap(task, user):
            actions.insert(1, "submit")
        return actions
    if role_id == "finance":
        actions = ["report", "source"]
        if task.get("assigneeId") == user.get("id") or task.get("riskDomain") in FINANCE_DOMAINS:
            actions.append("submit")
        return actions
    return ["report", "source"]


def task_visible_to_viewer(task: Dict[str, Any], viewer_id: str | None = None) -> bool:
    user = get_user(viewer_id)
    if not user:
        return True
    role_id = user.get("roleId")
    role_visible = role_id in set(task.get("visibleRoleIds") or [])
    user_visible = user.get("id") in set(task.get("visibleUserIds") or [])
    if role_id == "owner":
        return task.get("taskLayer") in {"owner_decision", "review_audit", "cycle_draft"} or role_visible
    if role_id == "manager":
        return role_visible and task_group_visible(task, user)
    if role_id == "operator":
        return user_visible or (task.get("taskLayer") == "operator_execution" and user_store_overlap(task, user))
    if role_id == "finance":
        return user_visible or role_visible or task.get("riskDomain") in FINANCE_DOMAINS
    if role_id == "observer":
        return task.get("status") in DONE_STATUS or role_visible
    return False


def project_task_for_viewer(task: Dict[str, Any], viewer_id: str | None = None) -> Dict[str, Any]:
    item = deepcopy(task)
    user = get_user(viewer_id)
    item["availableActions"] = available_actions_for_viewer(item, viewer_id)
    if user:
        item["viewerRoleId"] = user.get("roleId")
        item["viewerRoleName"] = user.get("roleName")
        item["viewerInsightDepth"] = user.get("insightDepth")
        if user.get("roleId") == "owner" and item.get("taskLayer") == "operator_execution":
            item["reason"] = "该任务属于运营执行层，老板端只保留汇总关注，不进入单条处理。"
        if user.get("roleId") == "operator" and item.get("assigneeId") != user.get("id") and not user_store_overlap(item, user):
            item["reason"] = "该任务不属于当前运营账号负责店铺。"
        if user.get("roleId") == "observer":
            item["reason"] = "该任务存在经营风险，已进入处理流程。"
            item["judgmentTags"] = ["已脱敏", "只读摘要"]
    return item


def list_tasks(active_only: bool = False, assignee_id: str | None = None, review_scope: bool = False, viewer_id: str | None = None) -> List[Dict[str, Any]]:
    tasks = [task for task in TASKS if not active_only or task.get("status") not in DONE_STATUS]
    if assignee_id:
        tasks = [task for task in tasks if task.get("assigneeId") == assignee_id]
    if review_scope:
        tasks = [task for task in tasks if task.get("status") == "待复核"]
    if viewer_id:
        tasks = [task for task in tasks if task_visible_to_viewer(task, viewer_id)]
    return [project_task_for_viewer(task, viewer_id) for task in sort_tasks(tasks)]


def list_logs() -> List[Dict[str, Any]]:
    return deepcopy(LOGS)


def find_task(task_id: str) -> Dict[str, Any] | None:
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


def create_log(payload: Dict[str, Any]) -> Dict[str, Any]:
    task = payload.get("task") or {}
    log = {"id": payload.get("id") or make_id("G"), "time": payload.get("time") or now_time(), "type": payload.get("type") or "任务记录", "source": payload.get("source") or task.get("source") or task.get("sourceModule") or "系统", "status": payload.get("status") or task.get("status") or "已记录", "level": payload.get("level") or task.get("priorityLevel") or "good", "imageLabel": payload.get("imageLabel") or task.get("imageLabel") or "记", "title": payload.get("title") or task.get("title") or task.get("productTitle") or "任务记录", "platform": payload.get("platform") or task.get("platform") or "经营单元", "store": payload.get("store") or task.get("store") or "任务池", "productId": payload.get("productId") or task.get("productId") or task.get("id") or "TASK", "action": payload.get("action") or "任务池动作", "reason": payload.get("reason") or task.get("reason") or "来自统一任务池。", "result": payload.get("result") or "已写入日志。", "route": payload.get("route") or task.get("sourceRoute") or "dashboard", "taskRoute": payload.get("taskRoute") or "business-actions", "operator": payload.get("operator") or task.get("assigneeName") or task.get("assignedByName") or "系统", "createdAt": now_iso()}
    LOGS.insert(0, log)
    del LOGS[200:]
    return deepcopy(log)


def create_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    task = normalize_task(payload)
    duplicate = find_open_task_by_key(task["dedupeKey"])
    if duplicate:
        duplicate["judgmentTags"] = list(dict.fromkeys([*(duplicate.get("judgmentTags") or []), *(task.get("judgmentTags") or [])]))[:8]
        duplicate["sourceTrail"] = list(dict.fromkeys([*(duplicate.get("sourceTrail") or []), task.get("sourceModule")]))
        duplicate["updatedAt"] = now_iso()
        duplicate["mergeCount"] = duplicate.get("mergeCount", 0) + 1
        create_log({"type": "任务合并", "task": duplicate, "status": "已合并", "action": f"{task.get('sourceModule')} 重复加入，已合并到现有任务", "reason": f"去重键：{duplicate['dedupeKey']}", "result": "未创建重复任务。"})
        result = deepcopy(duplicate)
        result["dedupeHit"] = True
        return result
    completed = find_completed_task_by_key(task["dedupeKey"])
    if completed:
        result = deepcopy(completed)
        result["dedupeHit"] = True
        result["candidateArchived"] = True
        result["candidateStatus"] = "completed_archived"
        create_log({"type": "任务归档拦截", "task": completed, "status": "已归档", "action": f"{task.get('sourceModule')} 尝试重复进入任务池", "reason": f"去重键已完成归档：{completed['dedupeKey']}", "result": "未重新创建任务；等待新一轮信号进入候选池。"})
        return result
    TASKS.append(task)
    if task.get("taskLayer") == "operator_execution":
        result_text = "模块预警已根据店铺归属进入对应运营待办，同时同步给店群总管可见。"
    elif task.get("taskLayer") == "manager_dispatch":
        result_text = "复盘 / 老板任务已进入店群总管任务池，等待拆分派发。"
    else:
        result_text = "任务已按角色权限进入对应任务池。"
    create_log({"type": "任务创建", "task": task, "status": "已加入任务池", "action": f"{task.get('sourceModule')} 创建任务：{task.get('taskType') or task.get('task') or task.get('title')}", "result": result_text})
    result = deepcopy(task)
    result["dedupeHit"] = False
    return result


def update_task(task_id: str, patch: Dict[str, Any], log_type: str = "任务更新", action: str = "任务已更新", result: str = "任务状态已同步。") -> Dict[str, Any] | None:
    task = find_task(task_id)
    if not task:
        return None
    task.update(patch)
    normalized = normalize_task(task)
    task.clear()
    task.update(normalized)
    task["updatedAt"] = now_iso()
    create_log({"type": log_type, "task": task, "status": task.get("status"), "action": action, "result": result})
    return deepcopy(task)


def split_task_for_operator(task_id: str, operator_id: str | None = None, note: str = "") -> Dict[str, Any] | None:
    task = find_task(task_id)
    if not task:
        return None
    operator = get_user(operator_id) if operator_id else operator_for_store(task.get("storeIds") or [], task.get("riskDomain"))
    if not operator:
        return None
    child = normalize_task({**task, "id": make_id("A"), "parentTaskId": task_id, "taskLayer": "operator_execution", "status": "待确认", "workflowStatus": "已派发", "assigneeId": operator["id"], "reviewerId": default_reviewer()["id"], "assignedById": default_reviewer()["id"], "assignmentNote": note or "由店群总管拆分而来。", "visibleRoleIds": ["manager", "operator"], "manualOrder": int(datetime.now().timestamp() * 1000), "dedupeKey": None})
    TASKS.append(child)
    task.setdefault("childTaskIds", []).append(child["id"])
    task["status"] = "已拆分"
    task["workflowStatus"] = "待派发"
    task["updatedAt"] = now_iso()
    create_log({"type": "任务拆分", "task": child, "status": child.get("status"), "action": f"{task.get('title')} 已拆分给 {operator['name']}", "result": "子任务进入运营待办，总管保留父任务复核视图。"})
    return deepcopy(child)


def assign_task(task_id: str, assignee_id: str | None = None, reviewer_id: str | None = None, operator_id: str | None = None, note: str = "") -> Dict[str, Any] | None:
    task = find_task(task_id)
    if not task:
        return None
    assignee = get_user(assignee_id) if assignee_id else operator_for_store(task.get("storeIds") or [], task.get("riskDomain"))
    reviewer = get_user(reviewer_id) if reviewer_id else default_reviewer()
    operator = get_user(operator_id) if operator_id else default_reviewer()
    if not assignee or not reviewer:
        return None
    return update_task(task_id, {"status": "处理中", "workflowStatus": "已派发", "taskLayer": "operator_execution", "assigneeId": assignee["id"], "reviewerId": reviewer["id"], "assignedById": operator.get("id") if operator else None, "assignmentNote": note, "assignedAt": now_iso(), "visibleRoleIds": ["manager", "operator"]}, "任务派发", f"任务已派发给 {assignee['name']}", "运营账号只看到自己负责店铺 / 自己承接的任务；处理后提交给店群总管复核。")


def submit_task(task_id: str, note: str = "", submitter_id: str | None = None) -> Dict[str, Any] | None:
    task = find_task(task_id)
    if not task:
        return None
    submitter_id = submitter_id or task.get("assigneeId") or operator_for_store(task.get("storeIds") or [], task.get("riskDomain"))["id"]
    return update_task(task_id, {"status": "待复核", "workflowStatus": "已提交", "submittedById": submitter_id, "submittedByName": user_display(submitter_id, "运营账号"), "submissionNote": note or "运营已完成处理，等待店群总管复核。", "submittedAt": now_iso()}, "任务提交", "运营已提交处理结果", "任务进入总管复核队列，完成前不会归档来源候选。")


def review_task(task_id: str, decision: str = "approve", note: str = "", reviewer_id: str | None = None) -> Dict[str, Any] | None:
    task = find_task(task_id)
    if not task:
        return None
    reviewer_id = reviewer_id or task.get("reviewerId") or default_reviewer()["id"]
    if decision in {"approve", "approved", "pass", "通过"}:
        return update_task(task_id, {"status": "已完成", "workflowStatus": "已归档", "candidateStatus": "completed_archived", "reviewedById": reviewer_id, "reviewedByName": user_display(reviewer_id, "店群总管"), "reviewNote": note or "复核通过，任务归档。", "reviewedAt": now_iso(), "completedAt": now_iso()}, "任务复核", "店群总管复核通过", "待办移除该任务，来源模块释放循环位，日志保留复盘记录。")
    if decision in {"return", "returned", "reject", "退回"}:
        return update_task(task_id, {"status": "处理中", "workflowStatus": "已退回", "reviewedById": reviewer_id, "reviewedByName": user_display(reviewer_id, "店群总管"), "reviewNote": note or "复核退回，需要运营补充处理。", "reviewedAt": now_iso()}, "任务退回", "店群总管退回复查", "任务回到运营处理状态，不释放来源模块循环位。")
    return None


def complete_task(task_id: str) -> Dict[str, Any] | None:
    return update_task(task_id, {"status": "已完成", "workflowStatus": "已归档", "completedAt": now_iso(), "candidateStatus": "completed_archived"}, "任务完成", "任务已完成并归档来源候选", "待办移除该任务，来源模块释放循环位，日志保留复盘记录。")


def pin_task(task_id: str) -> Dict[str, Any] | None:
    min_order = min([task.get("manualOrder", 9999) for task in TASKS] or [0])
    return update_task(task_id, {"manualOrder": min_order - 1}, "任务置顶", "任务已置顶", "首页和待办同步排序。")


def reorder_task(task_id: str, direction: str) -> Dict[str, Any] | None:
    active = sort_tasks([task for task in TASKS if task.get("status") not in DONE_STATUS])
    index = next((i for i, task in enumerate(active) if task.get("id") == task_id), -1)
    target_index = index - 1 if direction == "up" else index + 1
    if index < 0 or target_index < 0 or target_index >= len(active):
        return None
    current = active[index]
    target = active[target_index]
    current_order = current.get("manualOrder", index + 1)
    target_order = target.get("manualOrder", target_index + 1)
    current_ref = next(task for task in TASKS if task.get("id") == current.get("id"))
    target_ref = next(task for task in TASKS if task.get("id") == target.get("id"))
    current_ref["manualOrder"] = target_order
    target_ref["manualOrder"] = current_order
    current_ref["updatedAt"] = now_iso()
    target_ref["updatedAt"] = now_iso()
    create_log({"type": "任务排序", "task": current_ref, "status": current_ref.get("status"), "action": "任务顺序已调整", "result": "首页和待办同步排序。"})
    return deepcopy(current_ref)


def reset_tasks(viewer_id: str | None = None) -> Dict[str, Any]:
    global TASKS, LOGS
    TASKS = seed_tasks()
    LOGS = seed_logs()
    create_log({"type": "演示重置", "status": "已重置", "action": "服务端任务池已恢复默认演示数据", "result": "任务已重新按老板 / 总管 / 运营 / 财务 / 只读权限分发。"})
    return {"tasks": list_tasks(viewer_id=viewer_id), "logs": list_logs()}
