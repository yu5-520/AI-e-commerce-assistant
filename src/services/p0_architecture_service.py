"""P0 SaaS architecture decomposition service.

This service exposes the engineering target state as runtime-readable metadata.
It does not replace implementation work; it keeps the P0 architecture visible to
frontend, review pages, and future automated checks.
"""

from __future__ import annotations

from typing import Any

from src.core.context import UserContext
from src.repositories.scoped_repository import query_plan_for_context
from src.services.task_state_machine_service import task_persistence_summary

P0_ARCHITECTURE_VERSION = "5.3.0"


P0_LAYERS: list[dict[str, Any]] = [
    {
        "id": "P0-1",
        "name": "多租户身份与数据隔离",
        "status": "scaffolded",
        "target": "JWT/Session -> UserContext -> ScopedRepository -> tenant/store/deleted_at 强制过滤",
        "currentGap": "账号、角色、店铺仍以 demo account_service 为主，生产需落 tenants/users/roles/scopes 表。",
        "mustNot": ["不要在 Handler 手动拼 tenant_id", "不要只靠前端隐藏按钮做权限"],
    },
    {
        "id": "P0-2",
        "name": "软删除全局机制",
        "status": "soft_delete_mixin_scaffolded",
        "target": "所有核心表默认 deleted_at IS NULL；生产删除只软删除，Demo 可硬删。",
        "currentGap": "新增 SoftDeleteMixin 与 Alembic 初始表结构；现有 SQLite Demo 删除链路仍保留硬删能力以方便测试。",
        "mustNot": ["生产环境物理删除业务记录", "唯一索引忽略 deleted_at"],
    },
    {
        "id": "P0-3",
        "name": "任务系统持久化与状态机",
        "status": "task_evidence_trace_audit",
        "target": "tasks/task_events/task_logs/task_evidence 落库，状态变更与事件同事务。",
        "currentGap": "TaskRepository 写路径、任务流转、重置、证据提交、证据复核已写 trace_id / audit_logs；生产模型已新增 decision_tasks / task_events / task_evidence。",
        "mustNot": ["非法状态跃迁", "任务状态更新成功但审计事件丢失"],
    },
    {
        "id": "P0-4",
        "name": "报表导入事务链与 ImportJob",
        "status": "production_models_scaffolded",
        "target": "ImportJob -> DataVersion -> ImportedRows -> ProjectionJob -> AlertEvent -> TaskDraft -> AuditLog。",
        "currentGap": "ImportJob / ProjectionJob 已写入 trace_id 和 audit_logs；生产 SQLAlchemy 模型和 Alembic 表已新增，但 Repository 仍未切换到 PostgreSQL。",
        "mustNot": ["导入接口长时间阻塞", "重复执行生成重复任务"],
    },
    {
        "id": "P0-5",
        "name": "PostgreSQL 生产数据模型",
        "status": "postgres_alembic_scaffolded",
        "target": "SQLite 仅 Demo；生产使用 PostgreSQL + async SQLAlchemy + Alembic。",
        "currentGap": "新增 src/db/session.py、src/db/base.py、src/db/models.py、alembic.ini、alembic/env.py、初始 P0 schema migration 和 docs/POSTGRESQL_ALEMBIC.md。当前未替换 SQLite Demo 运行链路。",
        "mustNot": ["生产环境使用 SQLite", "无索引支撑待办/数据版本查询"],
    },
    {
        "id": "P0-6",
        "name": "Worker / Redis 后台任务",
        "status": "task_rag_trace_audit",
        "target": "导入、投影、预警、Agent 分析进入后台队列，任务幂等可重试。",
        "currentGap": "WorkerJob、WorkerTaskResult、rag_memory.staged 已写 audit_logs，并支持按 trace_id 查询结果；生产模型已新增 worker_jobs。",
        "mustNot": ["大报表阻塞 FastAPI 事件循环", "Worker 重试产生副作用"],
    },
    {
        "id": "P0-7",
        "name": "LLM Gateway 熔断降级与配额",
        "status": "llm_gateway_controls_scaffolded",
        "target": "熔断、限流、租户配额、结果缓存、Schema 校验、规则模板降级。",
        "currentGap": "新增 llm_gateway_service、llm_gateway_events、llm_gateway_cache、llm_circuit_breakers；生产模型已新增 llm_gateway_events。下一步扩展 provider 级熔断冷却和成本计量。",
        "mustNot": ["LLM 不可用导致核心链路中断", "AI 输出绕过 Schema 写业务库"],
    },
    {
        "id": "P0-8",
        "name": "Audit / Logs 双层体系",
        "status": "techlog_redaction_scaffolded",
        "target": "AuditLog 存业务审计，TechLog 输出 JSON，两者通过 trace_id 关联。",
        "currentGap": "新增 tech_log_service、tech_logs、递归敏感信息脱敏、/api/audit/tech-logs；生产模型已新增 audit_logs / tech_logs。",
        "mustNot": ["日志输出明文 Token/密码", "业务审计与技术日志混在一起"],
    },
    {
        "id": "P0-9",
        "name": "Nginx 前后端分离部署",
        "status": "deployment_security_gateway_scaffolded",
        "target": "Nginx 服务静态前端，/api 反代 FastAPI，HTTPS/CORS/限流/安全头统一配置。",
        "currentGap": "新增 Nginx 配置模板、部署说明、.env.example、Security Headers、FastAPI API RateLimit 和 /api/system/security；HTTPS 证书和生产域名仍需部署时配置。",
        "mustNot": ["生产用 FastAPI 直接托管全部前端资源", "CORS 全开放", "公网直接暴露 Uvicorn 端口"],
    },
]


IMPLEMENTATION_SEQUENCE = [
    "数据库基础层：Async SQLAlchemy / Alembic / TenantScopedMixin / SoftDeleteMixin 已新增",
    "生产模型：Tenant / User / Store / ImportJob / Task / Worker / Audit / TechLog / LLM Gateway 已建模",
    "下一步：SQLAlchemy Repository 逐步替换 SQLite Runtime Repository",
    "UserContext：JWT/Session 解析 tenant_id、user_id、role、store scope",
    "ScopedRepository：统一注入 tenant、store、deleted_at 过滤",
    "TaskRepository 生产实现：decision_tasks / task_events / task_evidence",
    "ImportJob 生产实现：import_jobs / projection_jobs / data_version / imported_rows",
    "WorkerJob 生产实现：worker_jobs 幂等、重试、认领",
    "Audit / TechLog 生产实现：audit_logs / tech_logs / trace_id",
    "部署安全网关：Nginx 模板、Security Headers、API RateLimit、/api/system/security、.env.example",
    "后续：前端系统状态页展示架构成熟度，或继续迁移 DataVersion / AlertEvent 生产表",
]


def p0_architecture_summary(ctx: UserContext) -> dict[str, Any]:
    query_plan = query_plan_for_context(ctx, table_alias="resource")
    return {
        "version": P0_ARCHITECTURE_VERSION,
        "title": "互联网大厂 SaaS P0 架构拆解",
        "runtimeMode": "postgres_alembic_scaffolded",
        "currentContext": ctx.to_dict(),
        "mandatoryScopePlan": {
            "where": query_plan.where,
            "params": query_plan.params,
            "rule": query_plan.rule,
        },
        "taskPersistence": task_persistence_summary(),
        "layers": P0_LAYERS,
        "implementationSequence": IMPLEMENTATION_SEQUENCE,
        "definitionOfDone": [
            "任何业务查询默认按 tenant_id + deleted_at + Data Scope 过滤。",
            "任务、任务事件、任务证据、任务日志全部落库，状态机拒绝非法跃迁。",
            "报表导入形成 ImportJob / DataVersion / AlertEvent / Task / AuditLog 全链路追踪。",
            "LLM 不可用时核心链路不受影响，AgentReport 使用规则模板降级。",
            "生产环境禁止 SQLite、Mock 密码、全局 fallback 假数据、无审计硬删除。",
            "生产流量应通过 Nginx / HTTPS / 安全头 / 限流进入 FastAPI。",
            "生产数据库迁移必须通过 Alembic 版本化执行。",
        ],
    }
