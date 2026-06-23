"""V9.9 delivery readiness contract."""

from __future__ import annotations

from typing import Any, Dict

from src.core.context import UserContext

V99_DELIVERY_VERSION = "9.9.0"

READINESS_AREAS: Dict[str, Any] = {
    "repository": ["version_source", "readme", "changelog", "ci_guard"],
    "runtime": ["api_version", "health", "route_mounting", "frontend_cache"],
    "product": ["stable_modules", "account_entry", "task_flow", "report_flow"],
    "enterprise": ["tier_boundary", "rag_boundary", "ops_boundary", "audit_boundary"],
    "deployment": ["env_check", "database_check", "rollback_plan", "acceptance_check"],
}

DELIVERY_STAGES = [
    "repo_check",
    "runtime_check",
    "api_check",
    "frontend_check",
    "enterprise_boundary_check",
    "deployment_check",
    "acceptance_report",
]

GO_LIVE_RULES = [
    "version and runtime must match",
    "health must expose current version",
    "enterprise boundaries must be documented",
    "critical changes must keep rollback notes",
    "production switch requires acceptance report",
]


def delivery_readiness_summary(ctx: UserContext) -> Dict[str, Any]:
    return {
        "version": V99_DELIVERY_VERSION,
        "name": "V9.9 delivery readiness consistency",
        "goal": "把 V9.1-V9.8 的仓库、运行态、前端、后端、企业边界和部署验收统一成最终交付检查契约。",
        "architectureEntry": "/api/architecture/v9/delivery-readiness",
        "stableProductEntries": ["/api/modules", "/api/accounts"],
        "readinessAreas": READINESS_AREAS,
        "deliveryStages": DELIVERY_STAGES,
        "goLiveRules": GO_LIVE_RULES,
        "nonGoals": ["不直接执行生产切换", "不自动修改客户数据", "不替代人工验收"],
        "context": ctx.to_dict(),
        "auditMeta": ctx.audit_meta(),
    }
