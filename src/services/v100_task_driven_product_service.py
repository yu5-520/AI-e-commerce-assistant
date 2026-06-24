"""V10.6 task-driven product contract."""

from __future__ import annotations

from typing import Any, Dict

from src.core.context import UserContext

V100_TASK_PRODUCT_VERSION = "10.6.0"

TASK_DRIVEN_PRINCIPLES = [
    "all user intervention must appear as a task",
    "system and Agent handle classification, labels, routing, refresh and audit",
    "users should not confirm tags or manually classify products by default",
    "frontend shows actions, not internal workflow complexity",
    "task cards are the primary product surface",
]

MINIMAL_NAVIGATION = ["dashboard", "reports", "operation", "tasks", "logs", "accounts", "system"]
NAVIGATION_LABELS = {"dashboard": "总览", "reports": "报表", "operation": "经营", "tasks": "任务", "logs": "日志", "accounts": "账号", "system": "系统"}
NAVIGATION_ROUTE_MAP = {"dashboard": "dashboard", "reports": "data-check", "operation": "operating-unit", "tasks": "business-actions", "logs": "business-report", "accounts": "accounts", "system": "system-status"}
COLLAPSED_OPERATION_ROUTES = ["business-products", "business-competitors", "business-listing", "business-traffic"]

USER_ACTIONS_BY_ROLE: Dict[str, Any] = {
    "owner": ["view", "follow", "confirm"],
    "manager": ["dispatch", "approve", "reject"],
    "operator": ["accept", "submit", "supplement"],
}

TASK_TYPES = ["business_action_task", "report_data_task", "tag_change_task", "weight_review_task", "cross_account_review_task", "system_confirmation_task"]
AGENT_AUTOMATION_SCOPE = ["vertical_category_tags", "store_weight_tags", "product_role_tags", "risk_tags", "task_intensity", "cross_account_flow", "audit_trace"]

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

V103_DASHBOARD_WORKBENCH_SECTIONS = ["todayPriorityTasks", "highRiskItems", "latestReportResult", "pendingReviewItems", "completionProgress"]
V103_DASHBOARD_RULES = [
    "dashboard answers what should be handled today",
    "priority tasks are shown before metrics",
    "high risk, report result, review and progress are secondary support blocks",
    "dashboard must route users into tasks instead of making them browse modules",
    "dashboard is a workbench, not a menu wall or architecture status page",
]

V104_IMPORT_TASK_FLOW = ["report_uploaded", "data_parsed_and_versioned", "alerts_detected", "tasks_created_or_merged", "modules_refreshed", "logs_written"]
V104_IMPORT_REFRESH_CONTRACT = {
    "updatedModules": ["dashboard", "operation", "tasks", "reports", "logs"],
    "frontendRefreshTargets": ["dashboard", "operating-unit", "business-actions", "data-check", "business-report"],
    "userMessage": "已更新，生成 X 个任务",
    "dataFlowDisplay": "collapsed_status_line",
}

V105_CROSS_ACCOUNT_FLOW = ["one_task_id_multiple_role_views", "operator_submit_routes_to_manager_review", "manager_review_routes_to_owner_progress", "role_views_sync_after_each_transition", "events_and_logs_keep_full_trace"]
V105_ROLE_VIEW_RULES = {
    "owner": {"surface": "progress", "actions": ["view", "follow", "confirm"]},
    "manager": {"surface": "dispatch_review", "actions": ["dispatch", "approve", "reject"]},
    "operator": {"surface": "execution", "actions": ["accept", "submit", "supplement"]},
}

V106_TASK_ACTION_RULES = [
    "one_primary_action_per_task_card",
    "one_secondary_action_allowed",
    "owner_view_follow_confirm",
    "manager_dispatch_approve_reject",
    "operator_accept_submit_supplement",
    "backend_keeps_full_events_and_logs",
]

TASK_FLOW_STAGES = ["data_uploaded", "agent_understands_context", "task_created", "role_view_synced", "user_action_submitted", "review_synced", "task_archived", "audit_written"]
NAVIGATION_COMPRESSION_RULES = ["sidebar keeps only seven product-level entries", "product, competitor, listing and traffic are collapsed under operation", "old module routes remain registered for internal jumps and detail links", "role scope maps to the compressed navigation before hiding links", "system complexity stays in system status, not daily operation views"]


def task_driven_product_summary(ctx: UserContext) -> Dict[str, Any]:
    return {
        "version": V100_TASK_PRODUCT_VERSION,
        "name": "V10 task-driven AI operating product",
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
        "dashboardWorkbenchSections": V103_DASHBOARD_WORKBENCH_SECTIONS,
        "dashboardRules": V103_DASHBOARD_RULES,
        "importTaskFlow": V104_IMPORT_TASK_FLOW,
        "importRefreshContract": V104_IMPORT_REFRESH_CONTRACT,
        "crossAccountFlow": V105_CROSS_ACCOUNT_FLOW,
        "roleViewRules": V105_ROLE_VIEW_RULES,
        "taskActionRules": V106_TASK_ACTION_RULES,
        "taskFlowStages": TASK_FLOW_STAGES,
        "nonGoals": ["不让用户默认确认标签", "不让用户手动维护分类作为主流程", "不把复杂流程节点暴露到经营界面", "不让用户手动选择跨账号流程节点", "不让任务卡堆满低频按钮"],
        "context": ctx.to_dict(),
        "auditMeta": ctx.audit_meta(),
    }
