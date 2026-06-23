"""V9.4 tier isolation consistency contract.

The service exposes the pricing-tier isolation contract as architecture metadata.
It does not enforce billing or execute business actions; it gives docs, CI, and
future feature-flag work one source of truth.
"""

from __future__ import annotations

from typing import Any, Dict

from src.core.context import UserContext

V94_TIER_ISOLATION_VERSION = "9.4.0"

TIER_CAPABILITIES: Dict[str, Dict[str, Any]] = {
    "starter": {
        "name": "基础版 / Starter",
        "billing": "monthly",
        "deploymentMode": "shared_saas",
        "ragNamespace": "shared_desensitized_rag",
        "dataIsolation": "tenant_runtime_scope + shared anonymized memory",
        "weightAlgorithms": {"productWeight": False, "storeWeight": False, "operatorWeight": False},
        "visibleCapabilities": ["basicReportAnalysis", "productIssueDetection", "productTaskGeneration", "sharedRagEvidence"],
        "hiddenCapabilities": ["storeWeight", "productWeight", "platformTrendDeepLink", "campaignTrendDeepLink", "approvalFlowDetail", "privateDeployment", "externalOpsAudit"],
        "serviceRule": "只提供基础报表整理、商品问题识别和商品任务生成。",
    },
    "professional": {
        "name": "专业版 / Professional",
        "billing": "annual",
        "deploymentMode": "multi_tenant_saas",
        "ragNamespace": "tenant_isolated_rag",
        "dataIsolation": "tenant_id + org_id + store_scope + tenant rag namespace",
        "weightAlgorithms": {"productWeight": True, "storeWeight": True, "operatorWeight": False},
        "visibleCapabilities": ["storeWeight", "productWeight", "platformTrend", "campaignTrend", "tenantRagEvidence", "taskIntensity", "agentEvidenceChain"],
        "paidMaintenance": ["ragTemplateRepair", "ragDataPatch", "industryTemplateAdjustment"],
        "hiddenCapabilities": ["privateDeployment", "privateRag", "externalOpsAdmin", "executiveChangeGate"],
        "serviceRule": "开放租户隔离 RAG、商品权重、店铺权重、平台趋势和活动趋势。",
    },
    "enterprise": {
        "name": "企业版 / Enterprise",
        "billing": "deployment_fee + annual_fee + ops_service",
        "deploymentMode": "private_deployment_or_customer_cloud",
        "ragNamespace": "private_customer_rag",
        "dataIsolation": "customer owned storage + private rag + strict audit trail",
        "weightAlgorithms": {"productWeight": True, "storeWeight": True, "operatorWeight": True},
        "visibleCapabilities": ["privateDeployment", "privateRag", "fullWeightSystem", "approvalGate", "executionFeedback", "reviewLog", "auditTrace", "externalOpsAdmin"],
        "opsBoundary": "受托运维只维护系统、配置、日志和留痕，不参与客户经营决策。",
        "executiveGate": "后端关键检查和更改只走客户高层授权。",
        "serviceRule": "完整私有化、完整权重系统、完整审批与审计链路。",
    },
}

ISOLATION_DIMENSIONS: Dict[str, Any] = {
    "featureFlags": ["basicReportAnalysis", "productWeight", "storeWeight", "operatorWeight", "platformTrend", "campaignTrend", "approvalGate", "executionFeedback", "privateDeployment"],
    "ragNamespaces": ["shared_desensitized_rag", "tenant_isolated_rag", "private_customer_rag"],
    "dataScopes": ["tenant_id", "org_id", "store_group_ids", "store_ids", "role_scope"],
    "auditDepth": ["basic_task_log", "tenant_audit_log", "private_audit_trail"],
    "deploymentModes": ["shared_saas", "multi_tenant_saas", "private_deployment_or_customer_cloud"],
}

FORBIDDEN_TIER_CROSSOVERS = [
    "starter must not access productWeight or storeWeight algorithms",
    "starter must not access tenant private RAG namespace",
    "professional must not access private customer RAG or private deployment controls",
    "enterprise external ops must not participate in business decisions",
    "frontend hiding alone is not isolation; backend capability gates must match tier",
]


def tier_isolation_contract_summary(ctx: UserContext) -> Dict[str, Any]:
    """Return the V9.4 tier isolation contract."""
    return {
        "version": V94_TIER_ISOLATION_VERSION,
        "name": "V9.4 tier isolation consistency",
        "goal": "把基础版、专业版、企业版的能力边界、RAG 命名空间、权重算法、部署模式和审计深度固定为系统级契约。",
        "nonGoals": [
            "不实现真实计费",
            "不自动开通客户套餐",
            "不把套餐隔离只做成前端隐藏",
            "不允许企业受托运维参与经营决策",
        ],
        "stableProductEntries": ["/api/modules", "/api/accounts"],
        "architectureEntry": "/api/architecture/v9/tier-isolation",
        "tiers": TIER_CAPABILITIES,
        "isolationDimensions": ISOLATION_DIMENSIONS,
        "forbiddenTierCrossovers": FORBIDDEN_TIER_CROSSOVERS,
        "modulePresentationRule": {
            "starter": "same modules, basic depth",
            "professional": "same modules, weighted operation depth",
            "enterprise": "same modules, private governance depth",
        },
        "context": ctx.to_dict(),
        "auditMeta": ctx.audit_meta(),
    }
