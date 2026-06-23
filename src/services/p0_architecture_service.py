"""P0 SaaS architecture decomposition service."""

from __future__ import annotations

from typing import Any

from src.core.context import UserContext
from src.repositories.scoped_repository import query_plan_for_context
from src.services.task_state_machine_service import task_persistence_summary

P0_ARCHITECTURE_VERSION = "5.3.2"


P0_LAYERS: list[dict[str, Any]] = [
    {
        "id": "P0-1",
        "name": "多租户身份与数据隔离",
        "status": "scaffolded",
        "target": "UserContext -> ScopedRepository -> tenant/store/deleted_at 查询约束",
        "currentGap": "Demo 身份仍来自 Header；生产身份体系等待 JWT / Session 接入。",
        "mustNot": ["Handler 手动拼租户条件", "只靠前端隐藏权限"],
    },
    {
        "id": "P0-2",
        "name": "软删除全局机制",
        "status": "soft_delete_mixin_scaffolded",
        "target": "生产表统一 deleted_at；Demo 保留测试清理能力。",
        "currentGap": "SoftDeleteMixin 已有，ProductionTaskRepository 软删除已写 deleted_at。",
        "mustNot": ["生产业务记录直接物理删除", "唯一索引忽略 deleted_at"],
    },
    {
        "id": "P0-3",
        "name": "任务系统持久化与状态机",
        "status": "task_repository_hybrid_mirror",
        "target": "decision_tasks / task_events / task_evidence 生产化。",
        "currentGap": "任务创建、流转、重置已支持 SQLite-first PostgreSQL mirror；默认 sqlite 模式仍跳过 mirror。",
        "mustNot": ["非法状态跃迁", "状态更新与事件分离"],
    },
    {
        "id": "P0-4",
        "name": "报表导入事务链与 ImportJob",
        "status": "sqlalchemy_repository_transition",
        "target": "ImportJob / ProjectionJob / DataVersion / AlertEvent 全链路追踪。",
        "currentGap": "ProductionImportJobRepository 已存在；写路径尚未双写。",
        "mustNot": ["导入接口长时间阻塞", "重复执行生成重复任务"],
    },
    {
        "id": "P0-5",
        "name": "PostgreSQL 生产数据模型",
        "status": "task_hybrid_mirror_ready",
        "target": "PostgreSQL + async SQLAlchemy + Alembic。",
        "currentGap": "新增 task_repository_mirror_service；/api/system/repositories 返回 taskHybridMirror。",
        "mustNot": ["生产使用 SQLite", "查询缺少必要索引"],
    },
    {
        "id": "P0-6",
        "name": "Worker / Redis 后台任务",
        "status": "sqlalchemy_repository_transition",
        "target": "worker_jobs 幂等、重试、认领生产化。",
        "currentGap": "ProductionWorkerJobRepository 可读；写路径尚未双写。",
        "mustNot": ["大报表阻塞事件循环", "重试产生副作用"],
    },
    {
        "id": "P0-7",
        "name": "LLM Gateway 控制层",
        "status": "llm_gateway_controls_scaffolded",
        "target": "配额、限流、缓存、熔断、Schema 校验。",
        "currentGap": "LLM Gateway 控制层已接入；生产 Repository 写路径后续再接。",
        "mustNot": ["模型不可用影响核心流程", "AI 输出绕过 Schema"],
    },
    {
        "id": "P0-8",
        "name": "Audit / TechLog",
        "status": "sqlalchemy_repository_transition",
        "target": "audit_logs / tech_logs / trace_id 生产化。",
        "currentGap": "ProductionAuditRepository 可按 trace_id 读取 audit_logs。",
        "mustNot": ["业务审计与技术日志混写", "日志缺少 trace_id"],
    },
    {
        "id": "P0-9",
        "name": "部署安全网关",
        "status": "deployment_security_gateway_scaffolded",
        "target": "Nginx 静态前端、/api 反代、CORS、限流、安全头。",
        "currentGap": "Nginx 模板、部署说明、.env.example、系统安全状态接口已存在。",
        "mustNot": ["生产直接暴露应用端口", "CORS 全开放"],
    },
]


IMPLEMENTATION_SEQUENCE = [
    "数据库基础层：Async SQLAlchemy / Alembic / TenantScopedMixin / SoftDeleteMixin 已新增",
    "生产模型：Tenant / User / Store / ImportJob / Task / Worker / Audit / TechLog / LLM Gateway 已建模",
    "Repository 过渡层：Task / ImportJob / WorkerJob / Audit 已新增生产实现",
    "Task hybrid mirror：任务创建 / 流转 / 重置 SQLite 成功后尝试 PostgreSQL mirror",
    "运行开关：DB_REPOSITORY_MODE=sqlite|hybrid|postgres，默认 sqlite 保证 Demo 稳定",
    "系统接口：/api/system/repositories 返回 taskHybridMirror，可选 check=true 检查 PostgreSQL 连接",
    "下一步：ImportJob / WorkerJob 写路径 hybrid 双写，或前端系统状态页展示架构成熟度",
]


def p0_architecture_summary(ctx: UserContext) -> dict[str, Any]:
    query_plan = query_plan_for_context(ctx, table_alias="resource")
    return {
        "version": P0_ARCHITECTURE_VERSION,
        "title": "互联网大厂 SaaS P0 架构拆解",
        "runtimeMode": "task_repository_hybrid_mirror",
        "currentContext": ctx.to_dict(),
        "mandatoryScopePlan": {"where": query_plan.where, "params": query_plan.params, "rule": query_plan.rule},
        "taskPersistence": task_persistence_summary(),
        "layers": P0_LAYERS,
        "implementationSequence": IMPLEMENTATION_SEQUENCE,
        "definitionOfDone": [
            "业务查询默认按 tenant_id + deleted_at + Data Scope 过滤。",
            "任务写路径 SQLite-first，并可在 hybrid/postgres 模式镜像到 PostgreSQL。",
            "报表导入形成 ImportJob / ProjectionJob / Task / Audit 全链路追踪。",
            "模型不可用时核心链路保持可运行。",
            "生产数据库迁移通过 Alembic 版本化执行。",
        ],
    }
