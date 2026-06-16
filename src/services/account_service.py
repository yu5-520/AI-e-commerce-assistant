"""Mock account, role, and permission service for the v2 collaboration layer.

This is a product contract, not a real login system. The frontend switches mock
accounts through `X-Mock-User-Id` so every module can render a specific role view
before SSO, tenant isolation, and production auth are connected.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Mapping

DEFAULT_USER_ID = "U001"

PERMISSIONS: List[Dict[str, str]] = [
    {"id": "view_all_stores", "name": "查看全部店群"},
    {"id": "view_managed_stores", "name": "查看负责店群"},
    {"id": "view_own_tasks", "name": "查看自己的任务"},
    {"id": "view_finance", "name": "查看数据 / 财务"},
    {"id": "view_org_risk", "name": "查看组织风险"},
    {"id": "view_command", "name": "查看任务指挥"},
    {"id": "dispatch_tasks", "name": "下发任务"},
    {"id": "assign_tasks", "name": "拆分派发"},
    {"id": "handle_tasks", "name": "处理任务"},
    {"id": "submit_tasks", "name": "提交处理结果"},
    {"id": "review_tasks", "name": "复核任务"},
    {"id": "manage_roles", "name": "管理角色权限"},
    {"id": "view_only", "name": "只读观察"},
]

PERMISSION_NAME_MAP = {item["id"]: item["name"] for item in PERMISSIONS}

EXECUTIVE_MODULES = [
    "dashboard",
    "store-overview",
    "task-command",
    "profit-budget",
    "org-efficiency",
    "review-audit",
    "accounts",
    "role-console",
]

OPERATION_MODULES = [
    "dashboard",
    "operating-unit",
    "data-check",
    "business-products",
    "business-competitors",
    "business-listing",
    "business-traffic",
    "business-actions",
    "business-report",
    "accounts",
]

ROLES: List[Dict[str, Any]] = [
    {
        "id": "owner",
        "name": "老板账号",
        "level": 1,
        "scope": "全部店群",
        "insightDepth": "owner_strategy",
        "insightName": "老板统筹视角",
        "description": "看店群盘面、利润预算、组织效率、任务闭环和审计，不进入一线运营细模块。",
        "permissions": ["view_all_stores", "view_finance", "view_org_risk", "view_command", "dispatch_tasks", "review_tasks", "manage_roles", "view_only"],
        "visibleModules": EXECUTIVE_MODULES,
        "allowedActions": ["查看店群总览", "查看任务指挥", "查看利润预算", "查看组织效率", "管理角色权限"],
        "hiddenFields": ["一线商品操作台", "一线上新操作台", "一线流量操作台", "一线竞品操作台"],
        "managementInsights": ["平台盘面", "店铺经营", "利润预算", "任务闭环", "组织效率", "复核审计"],
    },
    {
        "id": "manager",
        "name": "店群总管账号",
        "level": 2,
        "scope": "负责店群",
        "insightDepth": "team_management",
        "insightName": "店群管理视角",
        "description": "负责把经营信号拆成任务，派发运营并复核结果。",
        "permissions": ["view_managed_stores", "view_finance", "assign_tasks", "review_tasks", "manage_roles", "view_only"],
        "visibleModules": OPERATION_MODULES + ["role-console"],
        "allowedActions": ["拆分任务", "派发运营", "调整优先级", "复核通过", "退回补充"],
        "hiddenFields": ["全公司预算决策", "跨店群组织判断"],
        "managementInsights": ["店群任务积压", "运营处理质量", "重复预警", "复核效率", "流程卡点"],
    },
    {
        "id": "operator",
        "name": "运营账号",
        "level": 3,
        "scope": "自己的任务",
        "insightDepth": "execution_checklist",
        "insightName": "执行处理视角",
        "description": "只看到自己的任务、报告、检查清单和提交入口。",
        "permissions": ["view_own_tasks", "handle_tasks", "submit_tasks", "view_only"],
        "visibleModules": ["dashboard", "business-actions", "business-report", "accounts"],
        "allowedActions": ["查看任务报告", "提交处理结果", "补充说明", "重新提交"],
        "hiddenFields": ["全部店群", "其他运营任务", "财务利润", "组织判断"],
        "managementInsights": ["任务原因", "检查字段", "提交证据", "退回补充"],
    },
    {
        "id": "finance",
        "name": "数据 / 财务账号",
        "level": 3,
        "scope": "报表与财务数据",
        "insightDepth": "finance_risk",
        "insightName": "财务经营视角",
        "description": "查看利润、预算、ROI、退款成本和库存资金风险，不处理运营动作。",
        "permissions": ["view_finance", "view_only"],
        "visibleModules": ["dashboard", "store-overview", "profit-budget", "data-check", "business-report", "accounts"],
        "allowedActions": ["查看财务报告", "标记数据异常", "补充财务说明"],
        "hiddenFields": ["任务派发按钮", "运营复核按钮", "角色管理"],
        "managementInsights": ["利润承接", "退款成本", "ROI 可信度", "库存资金"],
    },
    {
        "id": "observer",
        "name": "只读观察账号",
        "level": 4,
        "scope": "被授权范围",
        "insightDepth": "summary_only",
        "insightName": "只读摘要视角",
        "description": "只能查看摘要、进度和日志结果，不能操作任务。",
        "permissions": ["view_only"],
        "visibleModules": ["dashboard", "store-overview", "review-audit", "business-report", "accounts"],
        "allowedActions": ["查看摘要", "查看日志"],
        "hiddenFields": ["财务细节", "任务责任链", "全部操作按钮"],
        "managementInsights": ["平台摘要", "店铺状态", "处理进度", "归档结果"],
    },
]

STORE_GROUPS: List[Dict[str, Any]] = [
    {"id": "G001", "name": "家居生活店群", "ownerId": "U001", "managerId": "U002", "storeIds": ["S001", "S002", "S003"]},
]

STORES: List[Dict[str, Any]] = [
    {"id": "S001", "name": "家居生活主店", "platform": "淘宝", "groupId": "G001"},
    {"id": "S002", "name": "家居百货店", "platform": "拼多多", "groupId": "G001"},
    {"id": "S003", "name": "家居好物号", "platform": "抖音小店", "groupId": "G001"},
]

USERS: List[Dict[str, Any]] = [
    {"id": "U001", "name": "老板", "roleId": "owner", "storeGroupIds": ["G001"], "storeIds": ["S001", "S002", "S003"], "status": "启用"},
    {"id": "U002", "name": "店群总管", "roleId": "manager", "storeGroupIds": ["G001"], "storeIds": ["S001", "S002", "S003"], "status": "启用"},
    {"id": "U003", "name": "运营 A", "roleId": "operator", "storeGroupIds": ["G001"], "storeIds": ["S001", "S002"], "status": "启用"},
    {"id": "U004", "name": "运营 B", "roleId": "operator", "storeGroupIds": ["G001"], "storeIds": ["S003"], "status": "启用"},
    {"id": "U005", "name": "数据财务", "roleId": "finance", "storeGroupIds": ["G001"], "storeIds": ["S001", "S002", "S003"], "status": "启用"},
    {"id": "U006", "name": "观察者", "roleId": "observer", "storeGroupIds": ["G001"], "storeIds": ["S001", "S002", "S003"], "status": "启用"},
]

ROLE_CHANGE_LOGS: List[Dict[str, Any]] = []


def clone(value: Any) -> Any:
    return deepcopy(value)


def permission_names(permission_ids: List[str]) -> List[str]:
    return [PERMISSION_NAME_MAP.get(item, item) for item in permission_ids]


def role_by_id(role_id: str | None) -> Dict[str, Any] | None:
    return next((role for role in ROLES if role["id"] == role_id), None)


def enrich_role(role: Dict[str, Any]) -> Dict[str, Any]:
    item = clone(role)
    item["permissionNames"] = permission_names(item.get("permissions", []))
    item["permissionSummary"] = "、".join(item["permissionNames"])
    return item


def enrich_user(user: Dict[str, Any]) -> Dict[str, Any]:
    item = clone(user)
    role = enrich_role(role_by_id(item.get("roleId")) or {})
    item["roleName"] = role.get("name", "未设置角色")
    item["roleLevel"] = role.get("level")
    item["insightDepth"] = role.get("insightDepth")
    item["insightName"] = role.get("insightName")
    item["permissions"] = role.get("permissions", [])
    item["permissionNames"] = role.get("permissionNames", [])
    item["visibleModules"] = role.get("visibleModules", [])
    item["allowedActions"] = role.get("allowedActions", [])
    item["hiddenFields"] = role.get("hiddenFields", [])
    item["managementInsights"] = role.get("managementInsights", [])
    item["scope"] = role.get("scope")
    return item


def list_roles() -> List[Dict[str, Any]]:
    return [enrich_role(role) for role in ROLES]


def list_permissions() -> List[Dict[str, str]]:
    return clone(PERMISSIONS)


def list_users() -> List[Dict[str, Any]]:
    return [enrich_user(user) for user in USERS]


def list_store_groups() -> List[Dict[str, Any]]:
    return clone(STORE_GROUPS)


def list_stores() -> List[Dict[str, Any]]:
    return clone(STORES)


def list_role_change_logs() -> List[Dict[str, Any]]:
    return clone(ROLE_CHANGE_LOGS)


def get_user(user_id: str | None) -> Dict[str, Any] | None:
    if not user_id:
        return None
    user = next((item for item in USERS if item["id"] == user_id), None)
    return enrich_user(user) if user else None


def resolve_user_id(user_id: str | None = None) -> str:
    return user_id if get_user(user_id) else DEFAULT_USER_ID


def user_id_from_headers(headers: Mapping[str, str] | None = None, fallback: str | None = None) -> str:
    headers = headers or {}
    raw = headers.get("x-mock-user-id") or headers.get("X-Mock-User-Id") or fallback
    return resolve_user_id(raw)


def current_user(user_id: str | None = None) -> Dict[str, Any]:
    return get_user(resolve_user_id(user_id)) or enrich_user(USERS[0])


def user_display(user_id: str | None, fallback: str = "未派发") -> str:
    user = get_user(user_id)
    if not user:
        return fallback
    return f"{user['name']} · {user['roleName']}"


def users_by_role(role_id: str) -> List[Dict[str, Any]]:
    return [user for user in list_users() if user.get("roleId") == role_id]


def default_operator(risk_domain: str | None = None) -> Dict[str, Any]:
    operators = users_by_role("operator")
    if risk_domain in {"流量", "上新"} and len(operators) > 1:
        return operators[1]
    return operators[0]


def default_reviewer() -> Dict[str, Any]:
    managers = users_by_role("manager")
    return managers[0]


def user_has_permission(user_id: str | None, permission: str) -> bool:
    user = current_user(user_id)
    return permission in user.get("permissions", [])


def role_view_for_user(user: Dict[str, Any]) -> Dict[str, Any]:
    role_id = user.get("roleId")
    pages = {
        "owner": {
            "headline": "老板统筹台",
            "summary": "先看平台、店铺、商品、订单、销售、利润、评论和库存的经营盘面，再进入任务、利润、组织和审计。",
            "sections": ["店群总览", "任务指挥", "利润预算", "组织效率", "复核审计"],
        },
        "manager": {
            "headline": "店群总管工作台",
            "summary": "看负责店群的一线经营模块，拆分任务、派发运营并复核结果。",
            "sections": ["店群经营", "商品", "竞品", "上新", "流量", "待办", "复核"],
        },
        "operator": {
            "headline": "运营执行台",
            "summary": "只看自己的任务、任务报告、提交入口和退回原因。",
            "sections": ["我的任务", "任务报告", "处理记录"],
        },
        "finance": {
            "headline": "数据 / 财务台",
            "summary": "看店铺经营盘面、利润、预算、ROI、退款成本、库存资金和数据异常，不处理运营动作。",
            "sections": ["店群总览", "利润预算", "报表异常", "日志"],
        },
        "observer": {
            "headline": "只读观察台",
            "summary": "只看摘要、进度和归档日志，不参与任务流转。",
            "sections": ["总览", "店群总览", "复核审计", "日志摘要"],
        },
    }
    return pages.get(role_id, pages["observer"])


def update_user_role(user_id: str, role_id: str, operator_id: str | None = None) -> Dict[str, Any] | None:
    user = next((item for item in USERS if item["id"] == user_id), None)
    role = role_by_id(role_id)
    if not user or not role:
        return None
    old_role = user.get("roleId")
    user["roleId"] = role_id
    ROLE_CHANGE_LOGS.insert(0, {"type": "角色变更", "userId": user_id, "oldRoleId": old_role, "newRoleId": role_id, "operatorId": operator_id or DEFAULT_USER_ID})
    return get_user(user_id)


def update_user_stores(user_id: str, store_ids: List[str], operator_id: str | None = None) -> Dict[str, Any] | None:
    user = next((item for item in USERS if item["id"] == user_id), None)
    valid = {store["id"] for store in STORES}
    if not user:
        return None
    user["storeIds"] = [store_id for store_id in store_ids if store_id in valid]
    ROLE_CHANGE_LOGS.insert(0, {"type": "店铺授权", "userId": user_id, "storeIds": user["storeIds"], "operatorId": operator_id or DEFAULT_USER_ID})
    return get_user(user_id)


def update_role_permissions(role_id: str, permissions: List[str], operator_id: str | None = None) -> Dict[str, Any] | None:
    role = role_by_id(role_id)
    valid = {permission["id"] for permission in PERMISSIONS}
    if not role:
        return None
    role["permissions"] = [permission for permission in permissions if permission in valid]
    ROLE_CHANGE_LOGS.insert(0, {"type": "权限模板", "roleId": role_id, "permissions": role["permissions"], "operatorId": operator_id or DEFAULT_USER_ID})
    return enrich_role(role)


def account_summary(user_id: str | None = None) -> Dict[str, Any]:
    user = current_user(user_id)
    return {
        "currentUser": user,
        "currentRoleView": role_view_for_user(user),
        "roles": list_roles(),
        "permissions": list_permissions(),
        "users": list_users(),
        "storeGroups": list_store_groups(),
        "stores": list_stores(),
        "roleChangeLogs": list_role_change_logs(),
        "taskFlow": ["店群盘面汇总", "异常字段进入任务指挥", "老板下发给总管", "总管拆分给运营", "运营提交后复核归档"],
        "boundary": {"authMode": "mock_account_context_header", "switchHeader": "X-Mock-User-Id", "realSsoConnected": False, "realEnterpriseTenantConnected": False, "permissionEnforcement": "mock_backend_scope_and_ui_actions"},
    }
