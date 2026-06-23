"""V9.5 RAG namespace isolation contract.

This service exposes the RAG namespace isolation contract as architecture
metadata. It does not implement a vector database ACL by itself; it defines the
runtime boundary that later ingestion, retrieval, write, and audit services must
follow.
"""

from __future__ import annotations

from typing import Any, Dict

from src.core.context import UserContext

V95_RAG_NAMESPACE_VERSION = "9.5.0"

RAG_NAMESPACES: Dict[str, Dict[str, Any]] = {
    "shared_desensitized_rag": {
        "tier": "starter",
        "owner": "platform",
        "storageMode": "shared",
        "allowedReads": ["starter", "professional", "enterprise"],
        "allowedWrites": ["platform_admin_reviewed"],
        "allowedContent": ["desensitized_cases", "generic_templates", "public_operation_patterns"],
        "forbiddenContent": ["tenant_raw_data", "private_customer_data", "pricing_secrets", "staff_performance_private_notes"],
        "rule": "只能存放脱敏后的通用经验，不允许写入租户原始数据或客户私有数据。",
    },
    "tenant_isolated_rag": {
        "tier": "professional",
        "owner": "tenant",
        "storageMode": "tenant_partitioned",
        "allowedReads": ["same_tenant_authorized_roles"],
        "allowedWrites": ["same_tenant_manager_reviewed", "paid_rag_maintenance"],
        "allowedContent": ["tenant_cases", "tenant_templates", "tenant_platform_trends", "tenant_campaign_trends"],
        "forbiddenContent": ["other_tenant_data", "private_customer_rag", "cross_tenant_raw_cases"],
        "rule": "按 tenant_id / org_id / store_scope 隔离，不允许跨租户检索和写入。",
    },
    "private_customer_rag": {
        "tier": "enterprise",
        "owner": "customer",
        "storageMode": "customer_owned_storage",
        "allowedReads": ["customer_authorized_roles", "external_ops_read_if_authorized"],
        "allowedWrites": ["customer_executive_approved", "external_ops_maintenance_approved"],
        "allowedContent": ["private_cases", "private_templates", "private_weight_reviews", "private_audit_memory"],
        "forbiddenContent": ["platform_training_reuse_without_contract", "external_ops_business_decision", "silent_deletion"],
        "rule": "客户侧存储，受托运维只维护系统和留痕，不参与经营决策。",
    },
}

RAG_ACCESS_GATES: Dict[str, Any] = {
    "namespaceResolver": ["tier", "tenant_id", "org_id", "store_scope", "role_scope"],
    "ingestionGate": ["source_type", "desensitization_status", "review_status", "target_namespace"],
    "retrievalGate": ["namespace", "tenant_scope", "role_scope", "feature_flag", "audit_context"],
    "writeGate": ["human_review", "quality_score", "metrics_change", "approval_status", "namespace_policy"],
    "templateMaintenanceGate": ["paid_maintenance_or_enterprise_ops", "change_reason", "before_after_diff", "approval_trace"],
    "deletionGate": ["no_silent_delete", "executive_or_owner_approval", "tombstone_log", "recoverability_note"],
}

FORBIDDEN_RAG_ACTIONS = [
    "starter writes tenant raw data into shared_desensitized_rag",
    "professional reads another tenant namespace",
    "professional reads private_customer_rag",
    "enterprise private RAG reused for platform training without contract",
    "external ops deletes or rewrites RAG memory silently",
    "frontend-only hiding used as RAG isolation",
]


def rag_namespace_isolation_summary(ctx: UserContext) -> Dict[str, Any]:
    """Return the V9.5 RAG namespace isolation contract."""
    return {
        "version": V95_RAG_NAMESPACE_VERSION,
        "name": "V9.5 RAG namespace isolation consistency",
        "goal": "把共享脱敏 RAG、租户隔离 RAG、客户私有 RAG 的读写、检索、沉淀、模板维护、删除和审计边界固定为系统级契约。",
        "nonGoals": [
            "不在本版本实现真实向量数据库 ACL",
            "不自动迁移客户 RAG 数据",
            "不把前端隐藏当作 RAG 隔离",
            "不允许受托运维绕过客户授权修改 private RAG",
        ],
        "stableProductEntries": ["/api/modules", "/api/accounts"],
        "architectureEntry": "/api/architecture/v9/rag-isolation",
        "namespaces": RAG_NAMESPACES,
        "accessGates": RAG_ACCESS_GATES,
        "forbiddenActions": FORBIDDEN_RAG_ACTIONS,
        "tierMapping": {
            "starter": "shared_desensitized_rag",
            "professional": "tenant_isolated_rag",
            "enterprise": "private_customer_rag",
        },
        "auditRule": "所有 RAG 检索、写入、模板维护和删除都必须保留 namespace、actor、tenant、store_scope、source、approval 和 before/after 记录。",
        "context": ctx.to_dict(),
        "auditMeta": ctx.audit_meta(),
    }
