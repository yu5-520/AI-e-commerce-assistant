"""Mock account, role, and permission service for the v2 collaboration layer.

This service is a product contract, not a real login system. The frontend can
switch mock accounts through `X-Mock-User-Id` so every module can render from a
specific role view before SSO, tenants, and production auth are connected.
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
    {"id": "dispatch_tasks", "name": "下发任务"},
    {"id": "assign_tasks", "name": "拆分派发"},
    {"id": "handle_tasks", "name": "处理任务"},
    {"id": "submit_tasks", "name": "提交处理结果"},
    {"id": "review_tasks", "name": "复核任务"},
    {"id": "view_only", "name": "只读观察"},
]

PERMISSION_NAME_MAP = {item["id"]: item["name"] for item in PERMISSIONS}

ROLES: List[Dict[str, Any]] = [
    {
        "id": "owner",
        "name": "老板账号",
        "level": 1,
        "scope": "全部店群",
        "insightDepth": "owner_strategy",
        "insightName": "老板战略视角",
        "description": "看全部店群、完整报告、组织瓶颈、利润风险和任务闭环，可以把任务下发给店群总管。",
        "permissions": ["view_all_stores", "view_finance", "view_org_risk", "dispatch_tasks", "review_tasks", "view_only"],
        "visibleModules": ["dashboard", "accounts", "operating-unit", "data-check", "business-products", "business-competitors", "business-listing", "business-traffic", "business-actions", "business-report"],
        "allowedActions": ["查看全部报告", "下发任务", "查看组织风险", "查看财务摘要", "查看复核结果"],
        "hiddenFields": [],
        "managementInsights": [
            "哪个店群拖累利润",
            "哪些任务反复返工",
            "广告预算是否在放大亏损商品",
            "售后问题是否升级成组织流程问题",
            "总管复核是否及时闭环",
        ],
    },
    {
        "id": "manager",
        "name": "店群总管账号",
        "level": 2,
        "scope": "负责店群",
        "insightDepth": "team_management",
        "insightName": "店群管理视角",
        "description": "接收老板下发任务，拆分给运营，跟踪处理进度，复核运营提交结果。",
        "permissions": ["view_managed_stores", "view_finance", "assign_tasks", "review_tasks", "view_only"],
        "visibleModules": ["dashboard", "accounts", "operating-unit", "data-check", "business-products", "business-competitors", "business-listing", "business-traffic", "business-actions", "business-report"],
        "allowedActions": ["拆分任务", "派发运营", "调整优先级", "复核通过", "退回补充"],
        "hiddenFields": ["跨店群组织风险", "老板级利润归因"],
        "managementInsights": [
            "哪个运营任务积压",
            "哪个商品反复出现同类预警",
            "任务是不是派错人",
            "运营提交是否缺少证据",
            "店群流程是否需要调整",
        ],
    },
    {
        "id": "operator",
        "name": "运营账号",
        "level": 3,
        "scope": "自己的任务",
        "insightDepth": "execution_checklist",
        "insightName": "执行处理视角",
        "description": "只看到分配给自己的任务、处理建议、检查清单和提交入口。",
        "permissions": ["view_own_tasks", "handle_tasks", "submit_tasks", "view_only"],
        "visibleModules": ["dashboard", "accounts", "business-actions", "business-report"],
        "allowedActions": ["查看任务报告", "提交处理结果", "补充说明", "重新提交"],
        "hiddenFields": ["全部店群", "其他运营任务", "人员绩效", "财务利润", "组织瓶颈"],
        "managementInsights": [
            "为什么这个任务被派给我",
            "需要检查哪些字段",
            "处理后要提交什么证据",
            "被退回时需要补充什么",
        ],
    },
    {
        "id": "finance",
        "name": "数据 / 财务账号",
        "level": 3,
        "scope": "报表与财务数据",
        "insightDepth": "finance_risk",
        "insightName": "财务经营视角",
        "description": "查看报表、利润、ROI、退款成本和库存资金风险，不直接处理运营任务。",
        "permissions": ["view_finance", "view_only"],
        "visibleModules": ["dashboard", "accounts", "data-check", "business-traffic", "business-report"],
        "allowedActions": ["查看财务报告", "标记数据异常", "补充财务说明"],
        "hiddenFields": ["任务派发按钮", "运营复核按钮", "人员管理评价"],
        "managementInsights": [
            "哪个商品看起来卖得好但实际亏钱",
            "退款成本是否吞掉利润",
            "广告 ROI 是否被虚高成交掩盖",
            "库存占用是否影响现金流",
        ],
    },
    {
        "id": "observer",
        "name": "只读观察账号",
        "level": 4,
        "scope": "被授权范围",
        "insightDepth": "summary_only",
        "insightName": "只读摘要视角",
        "description": "只能查看总览、部分报告和日志摘要，不能创建、派发、提交或复核任务。",
        "permissions": ["view_only"],
        "visibleModules": ["dashboard", "accounts", "business-report"],
        "allowedActions": ["查看摘要", "查看日志"],
        "hiddenFields": ["财务细节", "人员绩效", "任务责任链", "全部操作按钮"],
        "managementInsights": [
            "当前是否有风险",
            "任务是否已经进入流程",
            "处理结果是否已经归档",
        ],
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
            "headline": "老板视角",
            "summary": "看全部店群、利润风险、任务闭环和组织瓶颈。",
            "sections": ["全部账号", "店群授权", "组织任务链路", "人员处理效率", "权限边界"],
        },
        "manager": {
            "headline": "店群总管视角",
            "summary": "看自己负责的店群、待拆分任务、运营处理状态和复核队列。",
            "sections": ["我的店群", "我管理的运营", "待派发任务", "待复核任务", "退回记录"],
        },
        "operator": {
            "headline": "运营执行视角",
            "summary": "只看自己的任务、任务报告、检查清单、提交入口和退回原因。",
            "sections": ["我的权限", "我的任务范围", "可提交内容", "不可访问说明"],
        },
        "finance": {
            "headline": "数据 / 财务视角",
            "summary": "看报表、利润、退款成本、ROI、库存资金和数据异常，不处理运营任务。",
            "sections": ["数据权限", "财务口径", "异常报表", "不可操作说明"],
        },
        "observer": {
            "headline": "只读观察视角",
            "summary": "只看被授权摘要、部分报告和日志结果，不参与任务流转。",
            "sections": ["可查看页面", "只读范围", "不可操作说明"],
        },
    }
    return pages.get(role_id, pages["observer"])


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
        "taskFlow": [
            "老板查看店群总览和完整预警报告",
            "老板下发任务给店群总管",
            "店群总管拆分任务给运营",
            "运营处理后提交结果",
            "店群总管复核，通过后归档到日志",
        ],
        "boundary": {
            "authMode": "mock_account_context_header",
            "switchHeader": "X-Mock-User-Id",
            "realSsoConnected": False,
            "realEnterpriseTenantConnected": False,
            "permissionEnforcement": "mock_backend_scope_and_ui_actions",
        },
    }
