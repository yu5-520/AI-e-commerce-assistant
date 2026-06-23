"""V9.3 frontend module consistency contract.

The service exposes the frontend-module contract as architecture metadata. It
keeps V8/V9 backend capabilities attached to stable product modules instead of
creating new business modules for every backend capability.
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.core.context import UserContext

V93_FRONTEND_MODULE_VERSION = "9.3.0"

STABLE_FRONTEND_MODULES: List[Dict[str, Any]] = [
    {
        "route": "dashboard",
        "label": "总览",
        "api": "/api/modules/dashboard",
        "responsibility": "经营首页、最新导入、核心指标、当前任务队列和主状态摘要。",
        "enhancements": ["latestImport", "taskQueue", "riskSummary", "tierAwareSummary"],
    },
    {
        "route": "operating-unit",
        "label": "经营单元",
        "api": "/api/modules/operating-unit",
        "responsibility": "店铺、店群、平台和经营归属视图。",
        "enhancements": ["storeWeightSummary", "storeRole", "draggingProducts", "tenantScope"],
    },
    {
        "route": "business-products",
        "label": "商品",
        "api": "/api/modules/product",
        "responsibility": "商品经营问题、库存、点击、转化、ROI、退款和任务入口。",
        "enhancements": ["productWeightSummary", "storeImpact", "taskIntensity", "evidenceChain"],
    },
    {
        "route": "business-competitors",
        "label": "竞品",
        "api": "/api/modules/competitor",
        "responsibility": "竞品信号、价格、素材、上新和对照动作。",
        "enhancements": ["marketSignal", "linkedMetricEvidence", "candidateTaskEvidence"],
    },
    {
        "route": "business-listing",
        "label": "上新",
        "api": "/api/modules/listing",
        "responsibility": "已有商品测试、竞品对照上新和测试任务。",
        "enhancements": ["listingReadiness", "trendContext", "ragEvidence"],
    },
    {
        "route": "business-traffic",
        "label": "流量",
        "api": "/api/modules/traffic",
        "responsibility": "推广、活动、自然流量、流量波动和行动建议。",
        "enhancements": ["platformTrend", "campaignTrend", "trafficWeightImpact"],
    },
    {
        "route": "data-check",
        "label": "报表中心",
        "api": "/api/modules/report",
        "responsibility": "报表上传、字段预览、确认导入、版本记录、回滚和 Demo 清理。",
        "enhancements": ["dataVersionTrace", "importImpact", "flowTriggerSummary"],
    },
    {
        "route": "business-actions",
        "label": "待办",
        "api": "/api/modules/todo",
        "responsibility": "统一任务池、任务生命周期、提交证据、复核和完成归档。",
        "enhancements": ["taskIntensity", "approvalState", "executionEvidenceRequired", "reviewMetrics"],
    },
    {
        "route": "business-report",
        "label": "日志",
        "api": "/api/modules/log",
        "responsibility": "完成记录、执行回写、复盘结果、审计摘要和经验沉淀入口。",
        "enhancements": ["executionFeedback", "reviewLog", "ragMemoryCandidate", "auditTrace"],
    },
    {
        "route": "system-status",
        "label": "系统状态",
        "api": "/api/system/security",
        "responsibility": "安全、Repository、部署模式、RAG、权限、CI 和架构状态提示。",
        "enhancements": ["repositoryMode", "deploymentMode", "ragNamespace", "featureFlags", "auditStatus"],
    },
    {
        "route": "accounts",
        "label": "账号",
        "api": "/api/accounts",
        "responsibility": "账号、角色、店铺归属、可见范围和权限入口。",
        "enhancements": ["tierScope", "roleScope", "storeScope", "permissionBoundary"],
    },
]

TIER_PRESENTATION_DEPTH: Dict[str, Dict[str, Any]] = {
    "starter": {
        "name": "基础版 / Starter",
        "visibleDepth": "basic",
        "moduleRule": "只展示基础报表分析、商品问题和商品任务，不展示店铺/商品权重波动算法。",
        "enabledEnhancements": ["latestImport", "taskQueue", "basicProductIssue", "sharedRagEvidence"],
    },
    "professional": {
        "name": "专业版 / Professional",
        "visibleDepth": "weighted_operation",
        "moduleRule": "在经营单元、商品、任务详情和 Agent 报告中展示店铺/商品权重、平台趋势、活动趋势和租户 RAG 证据。",
        "enabledEnhancements": ["storeWeightSummary", "productWeightSummary", "platformTrend", "campaignTrend", "tenantRagEvidence", "taskIntensity"],
    },
    "enterprise": {
        "name": "企业版 / Enterprise",
        "visibleDepth": "private_governance",
        "moduleRule": "展示私有化部署状态、private RAG、受托运维、高层审批、审计留痕和完整执行复盘链。",
        "enabledEnhancements": ["privateDeployment", "privateRag", "externalOpsAdmin", "approvalGate", "auditTrace", "executionFeedback", "reviewLog"],
    },
}

FORBIDDEN_FRONTEND_EXPANSION = [
    "不要为店铺权重新增独立主模块，补强经营单元。",
    "不要为商品权重新增独立主模块，补强商品模块。",
    "不要为交叉验证新增独立主模块，补强任务详情和 Agent 报告。",
    "不要为执行回写新增独立主模块，补强日志和复盘。",
    "不要把 architecture/v8 调试入口当成运营主页面。",
]


def frontend_module_contract_summary(ctx: UserContext) -> Dict[str, Any]:
    """Return the V9.3 frontend module consistency contract."""
    return {
        "version": V93_FRONTEND_MODULE_VERSION,
        "name": "V9.3 frontend module consistency",
        "goal": "保持前端主模块稳定，把 V8/V9 后端能力作为套餐化增强字段补强到经营单元、商品、待办、详情、日志和系统状态。",
        "nonGoals": [
            "不新增前端业务主模块",
            "不把 V8 权重接口暴露成运营主页面",
            "不让基础版看到高阶权重算法细节",
            "不绕过后端套餐、RAG 和权限隔离",
        ],
        "stableEntry": "/api/modules",
        "accountEntry": "/api/accounts",
        "architectureEntry": "/api/architecture/v9/frontend-modules",
        "stableModules": STABLE_FRONTEND_MODULES,
        "tierPresentationDepth": TIER_PRESENTATION_DEPTH,
        "forbiddenFrontendExpansion": FORBIDDEN_FRONTEND_EXPANSION,
        "moduleEnhancementRule": {
            "storeWeight": "经营单元增强字段",
            "productWeight": "商品模块增强字段",
            "crossValidation": "详情页和 Agent 报告增强字段",
            "executionFeedback": "日志和复盘增强字段",
            "ragEvidence": "Agent 证据链增强字段",
            "tierScope": "所有模块通过后端套餐与权限控制显示深度",
        },
        "context": ctx.to_dict(),
        "auditMeta": ctx.audit_meta(),
    }
