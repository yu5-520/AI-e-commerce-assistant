"""V9.7 RAG audit rollback and accountability contract."""

from __future__ import annotations

from typing import Any, Dict

from src.core.context import UserContext

V97_RAG_AUDIT_VERSION = "9.7.0"

ROLLBACK_LIFECYCLE = [
    "rollback_request",
    "impact_scope_check",
    "approval_trace_check",
    "rollback_decision",
    "tombstone_write",
    "memory_restore_or_disable",
    "audit_review",
    "accountability_report",
]

ACCOUNTABILITY_ROLES = {
    "requester": "提出回滚原因和影响范围。",
    "reviewer": "复核证据、namespace、租户和风险。",
    "approver": "批准回滚或驳回。",
    "operator": "执行回滚，不参与经营决策。",
    "auditor": "复核留痕、责任链和结果。",
}

ROLLBACK_GATES: Dict[str, Any] = {
    "requestGate": ["memory_id", "namespace", "reason", "impact_scope", "evidence"],
    "approvalGate": ["reviewer_role", "approver_role", "decision", "comment", "timestamp"],
    "executionGate": ["before_hash", "after_hash", "tombstone_id", "recoverable_snapshot"],
    "auditGate": ["actor", "tenant_id", "store_scope", "operation", "result", "trace_id"],
    "accountabilityGate": ["responsible_role", "fault_type", "correction_action", "follow_up_owner"],
}

FORBIDDEN_ROLLBACKS = [
    "silent rollback without tombstone",
    "operator rollback without approval",
    "delete audit trail",
    "rewrite private customer memory without customer owner approval",
    "rollback to hide decision responsibility",
]


def rag_audit_rollback_summary(ctx: UserContext) -> Dict[str, Any]:
    return {
        "version": V97_RAG_AUDIT_VERSION,
        "name": "V9.7 RAG rollback audit and accountability consistency",
        "goal": "固定 RAG 记忆回滚、停用、恢复、审计复核和责任报告的主流程契约。",
        "nonGoals": ["不执行真实向量库删除", "不允许静默删除", "不绕过 V9.6 写入审批链"],
        "architectureEntry": "/api/architecture/v9/rag-audit-rollback",
        "stableProductEntries": ["/api/modules", "/api/accounts"],
        "rollbackLifecycle": ROLLBACK_LIFECYCLE,
        "accountabilityRoles": ACCOUNTABILITY_ROLES,
        "rollbackGates": ROLLBACK_GATES,
        "forbiddenRollbacks": FORBIDDEN_ROLLBACKS,
        "dependency": "V9.7 follows V9.6 memory promotion and V9.5 namespace isolation.",
        "context": ctx.to_dict(),
        "auditMeta": ctx.audit_meta(),
    }
