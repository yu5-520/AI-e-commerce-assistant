"""V9.2 backend main-flow consistency summary.

This service does not execute business actions. It exposes the intended backend
flow contract so docs, routes, CI, and future implementation work share one
source of truth.
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.core.context import UserContext

V92_BACKEND_FLOW_VERSION = "9.2.0"

FLOW_STAGES: List[Dict[str, Any]] = [
    {
        "id": "import_job",
        "name": "ImportJob",
        "entrypoints": ["/api/data/preview", "/api/data/import/confirm", "/api/data/import/report"],
        "owners": ["src/api/routes/data_import.py", "src/services/report_schema_service.py", "src/services/report_alert_service.py"],
        "contract": "报表预览、确认导入、创建数据版本，并触发后续模块投影、预警、趋势和任务候选。",
    },
    {
        "id": "data_version",
        "name": "DataVersion / RawRows",
        "entrypoints": ["/api/data/versions", "/api/data/import-records", "/api/data/versions/{data_version}/detail"],
        "owners": ["src/services/data_version_service.py", "src/services/report_alert_service.py"],
        "contract": "保存导入批次、原始行、字段映射、回滚状态和后续追溯上下文。",
    },
    {
        "id": "module_projection",
        "name": "ModuleProjection",
        "entrypoints": ["/api/modules/dashboard", "/api/modules/operating-unit", "/api/modules/product", "/api/modules/report"],
        "owners": ["src/api/routes/modules", "src/services/module_projection_service.py", "src/services/dashboard_service.py"],
        "contract": "把导入结果投影到总览、经营单元、商品、报表和任务视图，前端仍读取稳定模块入口。",
    },
    {
        "id": "alert_event",
        "name": "AlertEvent / TrendSignal",
        "entrypoints": ["/api/data/alerts", "/api/data/v3-summary", "/api/modules/trend"],
        "owners": ["src/services/report_alert_service.py", "src/services/trend_signal_service.py", "src/services/risk_task_service.py"],
        "contract": "从导入数据生成预警、趋势、经营信号和风险分级任务候选。",
    },
    {
        "id": "weight_signal",
        "name": "WeightSignal",
        "entrypoints": [
            "/api/architecture/v8/weight-snapshots",
            "/api/architecture/v8/weight-comparisons",
            "/api/architecture/v8/weight-rag-hits",
            "/api/architecture/v8/linked-relations",
            "/api/architecture/v8/weight-scores",
            "/api/architecture/v8/context-weights",
            "/api/architecture/v8/cross-validations",
        ],
        "owners": [
            "src/services/v80_weight_snapshot_service.py",
            "src/services/v81_weight_comparison_service.py",
            "src/services/v82_weight_rag_gate_service.py",
            "src/services/v83_linked_metric_relation_service.py",
            "src/services/v84_weight_score_service.py",
            "src/services/v85_context_weight_adjustment_service.py",
            "src/services/v86_cross_validation_service.py",
        ],
        "contract": "V8 权重能力作为后端增强层，为经营单元、商品、任务和 Agent 报告提供权重证据。",
    },
    {
        "id": "decision_task",
        "name": "DecisionTask / AgentReport",
        "entrypoints": ["/api/modules/agents", "/api/modules/agents/tasks/generate", "/api/modules/agents/{module}/{entity_id}", "/api/modules/task-report"],
        "owners": ["src/api/routes/modules/agents.py", "src/api/routes/modules/task_report.py", "src/services/task_agent_service.py", "src/services/module_agent_service.py", "src/services/action_plan_service.py"],
        "contract": "Agent 生成任务时读取模块数据、权重上下文、RAG 证据和 ActionPlan，不按模块套同一模板。",
    },
    {
        "id": "approval_flow",
        "name": "ApprovalFlow",
        "entrypoints": ["/api/approvals", "/api/architecture/v8/weight-approvals"],
        "owners": ["src/api/routes/approvals.py", "src/services/approval_lifecycle_service.py", "src/services/v88_weight_approval_service.py"],
        "contract": "高风险、权重动作和企业版关键操作必须进入审批门控；审批解锁执行，但不自动调用平台 API。",
    },
    {
        "id": "execution_feedback",
        "name": "ExecutionFeedback",
        "entrypoints": ["/api/architecture/v8/weight-executions", "/api/architecture/v8/weight-executions/{execution_id}/feedback"],
        "owners": ["src/services/v89_weight_execution_review_service.py", "src/services/execution_feedback_service.py"],
        "contract": "人工提交执行动作、证据、前后指标和结果；系统只记录回写，不直接改投产、商品、权限或 RAG 标准线。",
    },
    {
        "id": "review_log",
        "name": "ReviewLog / RagMemoryCandidate",
        "entrypoints": ["/api/architecture/v8/weight-execution-reviews", "/api/modules/rag-memory", "/api/modules/feedback-flywheel", "/api/modules/log"],
        "owners": ["src/services/v89_weight_execution_review_service.py", "src/api/routes/modules/rag_memory.py", "src/api/routes/modules/feedback_flywheel.py", "src/api/routes/modules/log.py"],
        "contract": "复盘结果、任务经验和候选记忆进入人工复核链路；RAG 候选不能自动批准入库。",
    },
]


def backend_flow_summary(ctx: UserContext) -> Dict[str, Any]:
    """Return the V9.2 backend flow contract for architecture visibility."""
    return {
        "version": V92_BACKEND_FLOW_VERSION,
        "name": "V9.2 backend main-flow consistency",
        "goal": "把 V8 权重能力从旁路架构接口收束为后端增强层，并固定导入、投影、权重、任务、Agent、审批、执行、复盘、RAG 候选的主流程契约。",
        "nonGoals": [
            "不新增前端主模块",
            "不继续扩展 V8 新算法",
            "不自动调用平台 API 执行经营动作",
            "不自动改写 RAG 标准线或权重规则",
        ],
        "stableFrontendEntrypoints": ["/api/modules", "/api/accounts"],
        "architectureEntrypoint": "/api/architecture/v9/backend-flow",
        "flowStages": FLOW_STAGES,
        "moduleEnhancementRule": {
            "operatingUnit": "读取店铺权重摘要和店铺角色，不新增店铺权重主模块。",
            "product": "读取商品权重摘要、店铺影响和处理强度，不新增商品权重主模块。",
            "todo": "读取任务强度、审批状态和证据要求。",
            "taskReport": "读取交叉验证、RAG 证据和 Agent 方案。",
            "log": "读取执行回写、复盘结果和 RAG 候选状态。",
        },
        "context": ctx.to_dict(),
        "auditMeta": ctx.audit_meta(),
    }
