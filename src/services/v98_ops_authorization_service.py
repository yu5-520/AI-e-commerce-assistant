"""V9.8 enterprise ops authorization contract."""

from __future__ import annotations

from typing import Any, Dict

from src.core.context import UserContext

V98_OPS_AUTH_VERSION = "9.8.0"

ENTERPRISE_ROLES: Dict[str, Dict[str, Any]] = {
    "owner_high_level": {
        "type": "decision",
        "canApprove": ["system_config_change", "private_memory_change", "critical_scope_change"],
        "cannotDo": ["silent_data_patch", "direct_database_edit_without_trace"],
    },
    "business_manager": {
        "type": "business_review",
        "canApprove": ["task_dispatch", "review_result", "business_scope_request"],
        "cannotDo": ["system_backend_change", "ops_permission_change"],
    },
    "operator": {
        "type": "execution",
        "canDo": ["task_execute", "evidence_submit", "result_feedback"],
        "cannotDo": ["approve_own_result", "change_system_rule", "change_memory_rule"],
    },
    "external_ops_admin": {
        "type": "system_maintenance",
        "canDo": ["deploy", "backup", "export_audit", "authorized_config_apply"],
        "cannotDo": ["business_decision", "approve_business_action", "edit_review_result", "erase_trace"],
    },
    "audit_observer": {
        "type": "audit_readonly",
        "canDo": ["read_audit", "export_report", "verify_trace"],
        "cannotDo": ["change_data", "approve_action", "execute_task"],
    },
}

AUTHORIZATION_FLOW = [
    "change_request",
    "risk_scope_check",
    "owner_decision",
    "ops_apply_if_authorized",
    "audit_trace_write",
    "business_visibility_sync",
    "post_change_review",
]

SEPARATION_RULES = [
    "business execution and system maintenance must be separated",
    "external ops can apply authorized changes but cannot approve business decisions",
    "owner approval is required for critical backend or private memory changes",
    "audit observer is read-only",
    "all critical changes must produce trace records",
]


def ops_authorization_summary(ctx: UserContext) -> Dict[str, Any]:
    return {
        "version": V98_OPS_AUTH_VERSION,
        "name": "V9.8 enterprise ops authorization consistency",
        "goal": "固定企业版高层授权、业务执行、受托运维和审计观察之间的四权分离契约。",
        "architectureEntry": "/api/architecture/v9/ops-authorization",
        "stableProductEntries": ["/api/modules", "/api/accounts"],
        "roles": ENTERPRISE_ROLES,
        "authorizationFlow": AUTHORIZATION_FLOW,
        "separationRules": SEPARATION_RULES,
        "nonGoals": ["不实现真实 IAM", "不允许受托运维参与经营决策", "不允许静默修改关键配置"],
        "context": ctx.to_dict(),
        "auditMeta": ctx.audit_meta(),
    }
