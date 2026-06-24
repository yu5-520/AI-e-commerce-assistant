"""V10.2 task-driven product contract.

V10 turns the system from architecture readiness into a task-driven product.
Users should not configure labels, categories, workflow nodes, or routing rules.
The system and Agent translate data changes into tasks; users finish work through tasks.
V10.1 compresses the frontend navigation into a few product entries.
V10.2 makes the UI hierarchy productized: compact title, dominant action, large task surface.
"""

from __future__ import annotations

from typing import Any, Dict

from src.core.context import UserContext

V100_TASK_PRODUCT_VERSION = "10.2.0"

TASK_DRIVEN_PRINCIPLES = [
    "all user intervention must appear as a task",
    "system and Agent handle classification, labels, routing, refresh and audit",
    "users should not confirm tags or manually classify products by default",
    "frontend shows actions, not internal workflow complexity",
    "task cards are the primary product surface",
]

MINIMAL_NAVIGATION = [
    "dashboard",
    "reports",
    "operation",
    "tasks",
    "logs",
    "accounts",
    "system",
]

NAVIGATION_LABELS = {
    "dashboard": "总览",
    "reports": "报表",
    "operation": "经营",
    "tasks": "任务",
    "logs": "日志",
    "accounts": "账号",
    "system": "系统",
}

NAVIGATION_ROUTE_MAP = {
    "dashboard": "dashboard",
    "reports": "data-check",
    "operation": "operating-unit",
    "tasks": "business-actions",
    "logs": "business-report",
    "accounts": "accounts",
    "system": "system-status",
}

COLLAPSED_OPERATION_ROUTES = [
    "business-products",
    "business-competitors",
    "business-listing",
    "business-traffic",
]

USER_ACTIONS_BY_ROLE: Dict[str, Any] = {
    "owner": ["view", "follow", "confirm"],
    "manager": ["dispatch", "approve", "reject"],
    "operator": ["accept", "submit", "supplement"],
}

TASK_TYPES = [
    "business_action_task",
    "report_data_task",
    "tag_change_task",
    "weight_review_task",
    "cross_account_review_task",
    "system_confirmation_task",
]

AGENT_AUTOMATION_SCOPE = [
    "vertical_category_tags",
    "store_weight_tags",
    "product_role_tags",
    "risk_tags",
    "task_intensity",
    "cross_account_flow",
    "audit_trace",
]

FRONTEND_LAYOUT_RULES = {
    "titleArea": "compact",
    "explanationText": "minimized",
    "mainActionArea": "dominant",
    "dataFlow": "collapsed_by_default",
    "systemInfo": "system_page_only",
    "taskCard": "primary_surface",
    "visualRatio": "main_70_aux_20_title_10",
    "firstScreenGoal": "user_knows_next_action",
}

V102_UI_PRODUCTIZATION_RULES = [
    "topbar and page hero stay compact",
    "main action and task cards occupy the strongest visual weight",
    "data flow is summarized in one line or collapsed into details",
    "system status and version detail do not compete with daily operation",
    "each page keeps a clear primary action above secondary data",
]

TASK_FLOW_STAGES = [
    "data_uploaded",
    "agent_understands_context",
    "task_created",
    "role_view_synced",
    "user_action_submitted",
    "review_synced",
    "task_archived",
    "audit_written",
]

NAVIGATION_COMPRESSION_RULES = [
    "sidebar keeps only seven product-level entries",
    "product, competitor, listing and traffic are collapsed under operation",
    "old module routes remain registered for internal jumps and detail links",
    "role scope maps to the compressed navigation before hiding links",
    "system complexity stays in system status, not daily operation views",
]


def task_driven_product_summary(ctx: UserContext) -> Dict[str, Any]:
    return {
        "version": V100_TASK_PRODUCT_VERSION,
        "name": "V10 task-driven AI operating product",
        "goal": "把 V9 的企业级架构验收收束成任务驱动产品：用户只处理任务，系统和 Agent 自动完成分类、标签、判断、流转、刷新和留痕。",
        "architectureEntry": "/api/architecture/v10/task-driven-product",
        "stableProductEntries": ["/api/modules", "/api/accounts", "/api/health"],
        "principles": TASK_DRIVEN_PRINCIPLES,
        "minimalNavigation": MINIMAL_NAVIGATION,
        "navigationLabels": NAVIGATION_LABELS,
        "navigationRouteMap": NAVIGATION_ROUTE_MAP,
        "collapsedOperationRoutes": COLLAPSED_OPERATION_ROUTES,
        "navigationCompressionRules": NAVIGATION_COMPRESSION_RULES,
        "userActionsByRole": USER_ACTIONS_BY_ROLE,
        "taskTypes": TASK_TYPES,
        "agentAutomationScope": AGENT_AUTOMATION_SCOPE,
        "frontendLayoutRules": FRONTEND_LAYOUT_RULES,
        "uiProductizationRules": V102_UI_PRODUCTIZATION_RULES,
        "taskFlowStages": TASK_FLOW_STAGES,
        "nonGoals": [
            "不让用户默认确认标签",
            "不让用户手动维护分类作为主流程",
            "不把复杂流程节点暴露到经营界面",
            "不把系统能力展示替代用户任务引导",
            "不把商品、竞品、上新、流量继续放在主导航里",
            "不让标题、说明和数据流转抢占主操作空间",
        ],
        "context": ctx.to_dict(),
        "auditMeta": ctx.audit_meta(),
    }
