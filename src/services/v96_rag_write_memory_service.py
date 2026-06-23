"""V9.6 RAG write approval and memory promotion contract."""

from __future__ import annotations

from typing import Any, Dict

from src.core.context import UserContext

V96_RAG_WRITE_VERSION = "9.6.0"

MEMORY_LIFECYCLE = [
    "rag_memory_candidate",
    "quality_check",
    "namespace_policy_check",
    "human_review",
    "approval_decision",
    "promoted_memory",
    "audit_record",
    "rollback_tombstone",
]

WRITE_POLICIES: Dict[str, Dict[str, Any]] = {
    "shared_desensitized_rag": {
        "requiredReview": ["desensitization_review", "platform_admin_review"],
        "promotionRule": "only generic and desensitized cases can be promoted",
        "rejectIf": ["raw_tenant_data", "private_customer_data", "staff_private_note"],
    },
    "tenant_isolated_rag": {
        "requiredReview": ["tenant_manager_review", "namespace_policy_check"],
        "promotionRule": "only same tenant reviewed cases can be promoted",
        "rejectIf": ["other_tenant_data", "private_customer_data", "missing_tenant_scope"],
    },
    "private_customer_rag": {
        "requiredReview": ["customer_owner_review", "executive_or_ops_authorization"],
        "promotionRule": "only customer authorized private cases can be promoted",
        "rejectIf": ["no_customer_approval", "platform_reuse_without_contract", "silent_ops_change"],
    },
}

APPROVAL_GATES = {
    "candidateGate": ["source", "namespace", "tenant_id", "store_scope", "evidence", "metrics_change"],
    "qualityGate": ["quality_score", "repeatability", "risk_label", "desensitization_status"],
    "humanGate": ["reviewer_role", "approval_status", "comment", "timestamp"],
    "promotionGate": ["before_hash", "after_hash", "memory_id", "namespace", "audit_id"],
    "rollbackGate": ["rollback_reason", "tombstone_log", "recoverable_snapshot", "owner_approval"],
}

FORBIDDEN_WRITES = [
    "auto promote candidate without human review",
    "write memory without namespace",
    "write shared memory with raw tenant data",
    "write private memory without customer approval",
    "delete memory without tombstone",
]


def rag_write_memory_summary(ctx: UserContext) -> Dict[str, Any]:
    return {
        "version": V96_RAG_WRITE_VERSION,
        "name": "V9.6 RAG write approval and memory promotion consistency",
        "goal": "固定 RAG 候选记忆、人工复核、审批、正式沉淀、审计和回滚的主流程契约。",
        "nonGoals": ["不自动推广记忆", "不实现真实向量库写入", "不绕过 V9.5 namespace 隔离"],
        "architectureEntry": "/api/architecture/v9/rag-write-memory",
        "stableProductEntries": ["/api/modules", "/api/accounts"],
        "memoryLifecycle": MEMORY_LIFECYCLE,
        "writePolicies": WRITE_POLICIES,
        "approvalGates": APPROVAL_GATES,
        "forbiddenWrites": FORBIDDEN_WRITES,
        "dependency": "V9.6 must follow V9.5 RAG namespace isolation before memory promotion.",
        "context": ctx.to_dict(),
        "auditMeta": ctx.audit_meta(),
    }
