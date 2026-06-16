"""Mock account, role, and permission service for the v2 collaboration layer.

This is intentionally lightweight. It gives the product a stable account and
permission contract before real authentication, SSO, or enterprise tenant
storage is connected.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

PERMISSIONS: List[Dict[str, str]] = [
    {"id": "view_all_stores", "name": "查看全部店群"},
    {"id": "dispatch_tasks", "name": "下发任务"},
    {"id": "assign_tasks", "name": "拆分派发"},
    {"id": "handle_tasks", "name": "处理自己的任务"},
    {"id": "submit_tasks", "name": "提交处理结果"},
    {"id": "review_tasks", "name": "复核任务"},
    {"id": "view_finance", "name": "查看数据 / 财务"},
    {"id": "view_only", "name": "只读观察"},
]

ROLES: List[Dict[str, Any]] = [
    {
        "id": "owner",
        "name": "老板账号",
        "level": 1,
        "scope": "全部店群",
        "description": "看店群总览、完整报告、任务流转和复核结果，可以把任务下发给店群总管。",
        "permissions": ["view_all_stores", "dispatch_tasks", "review_tasks", "view_finance", "view_only"],
    },
    {
        "id": "manager",
        "name": "店群总管账号",
        "level": 2,
        "scope": "负责店群",
        "description": "接收老板下发任务，拆分给运营，复核运营提交结果。",
        "permissions": ["assign_tasks", "review_tasks", "view_finance", "view_only"],
    },
    {
        "id": "operator",
        "name": "运营账号",
        "level": 3,
        "scope": "自己的任务",
        "description": "只处理分配给自己的商品、竞品、上新、流量任务，并提交处理结果。",
        "permissions": ["handle_tasks", "submit_tasks", "view_only"],
    },
    {
        "id": "finance",
        "name": "数据 / 财务账号",
        "level": 3,
        "scope": "报表与财务数据",
        "description": "查看 ERP / CRM 报表、财务口径和数据异常，不直接处理运营任务。",
        "permissions": ["view_finance", "view_only"],
    },
    {
        "id": "observer",
        "name": "只读观察账号",
        "level": 4,
        "scope": "被授权范围",
        "description": "只能查看看板、报告和日志，不能创建、派发、提交或复核任务。",
        "permissions": ["view_only"],
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

CURRENT_USER_ID = "U001"


def clone(value: Any) -> Any:
    return deepcopy(value)


def role_by_id(role_id: str | None) -> Dict[str, Any] | None:
    return next((role for role in ROLES if role["id"] == role_id), None)


def enrich_user(user: Dict[str, Any]) -> Dict[str, Any]:
    item = clone(user)
    role = role_by_id(item.get("roleId")) or {}
    item["roleName"] = role.get("name", "未设置角色")
    item["roleLevel"] = role.get("level")
    item["permissions"] = role.get("permissions", [])
    item["permissionNames"] = [permission["name"] for permission in PERMISSIONS if permission["id"] in item["permissions"]]
    return item


def list_roles() -> List[Dict[str, Any]]:
    return clone(ROLES)


def list_permissions() -> List[Dict[str, str]]:
    return clone(PERMISSIONS)


def list_users() -> List[Dict[str, Any]]:
    return [enrich_user(user) for user in USERS]


def list_store_groups() -> List[Dict[str, Any]]:
    return clone(STORE_GROUPS)


def list_stores() -> List[Dict[str, Any]]:
    return clone(STORES)


def get_user(user_id: str | None) -> Dict[str, Any] | None:
    if not user_id:
        return None
    user = next((item for item in USERS if item["id"] == user_id), None)
    return enrich_user(user) if user else None


def current_user() -> Dict[str, Any]:
    return get_user(CURRENT_USER_ID) or enrich_user(USERS[0])


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
    user = get_user(user_id) or current_user()
    return permission in user.get("permissions", [])


def account_summary() -> Dict[str, Any]:
    return {
        "currentUser": current_user(),
        "roles": list_roles(),
        "permissions": list_permissions(),
        "users": list_users(),
        "storeGroups": list_store_groups(),
        "stores": list_stores(),
        "taskFlow": [
            "老板查看店群总览和完整预警报告",
            "老板下发任务给店群总管",
            "店群总管拆分任务给运营",
            "运营处理后提交结果",
            "店群总管复核，通过后归档到日志",
        ],
        "boundary": {
            "authMode": "mock_account_context",
            "realSsoConnected": False,
            "realEnterpriseTenantConnected": False,
            "permissionEnforcement": "route_contract_first_ui_visible",
        },
    }
