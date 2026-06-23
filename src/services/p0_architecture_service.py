"""P0 SaaS architecture decomposition service."""

from __future__ import annotations

from typing import Any

from src.core.context import UserContext
from src.repositories.scoped_repository import query_plan_for_context
from src.services.task_state_machine_service import task_persistence_summary

P0_ARCHITECTURE_VERSION = "5.3.4"

P0_LAYERS: list[dict[str, Any]] = [
    {"id": "P0-1", "name": "多租户身份与数据隔离", "status": "scaffolded", "target": "UserContext + ScopedRepository", "currentGap": "Demo 身份仍来自 Header。"},
    {"id": "P0-2", "name": "软删除机制", "status": "soft_delete_mixin_scaffolded", "target": "deleted_at 统一字段", "currentGap": "生产模型和 Repository 已有软删除字段。"},
    {"id": "P0-3", "name": "任务系统", "status": "task_repository_hybrid_mirror", "target": "decision_tasks", "currentGap": "任务创建、流转、重置已支持 SQLite-first mirror。"},
    {"id": "P0-4", "name": "报表导入", "status": "import_job_hybrid_mirror", "target": "import_jobs", "currentGap": "ImportJob 创建、完成、失败已支持 SQLite-first mirror。"},
    {"id": "P0-5", "name": "PostgreSQL 数据模型", "status": "audit_tech_hybrid_mirror_ready", "target": "PostgreSQL + Alembic", "currentGap": "AuditLog / TechLog upsert 已补齐。"},
    {"id": "P0-6", "name": "Worker 队列", "status": "worker_job_hybrid_mirror", "target": "worker_jobs", "currentGap": "enqueue / claim / complete / fail / retry 已支持 mirror。"},
    {"id": "P0-7", "name": "LLM Gateway", "status": "llm_gateway_controls_scaffolded", "target": "配额、限流、缓存、熔断、Schema 校验", "currentGap": "控制层已接入。"},
    {"id": "P0-8", "name": "Audit / TechLog", "status": "audit_tech_hybrid_mirror", "target": "audit_logs / tech_logs", "currentGap": "业务审计和技术日志写路径已支持 mirror。"},
    {"id": "P0-9", "name": "部署入口", "status": "deployment_gateway_scaffolded", "target": "Nginx + FastAPI", "currentGap": "模板和状态接口已存在。"},
]

IMPLEMENTATION_SEQUENCE = [
    "Task hybrid mirror 已完成",
    "ImportJob hybrid mirror 已完成",
    "WorkerJob hybrid mirror 已完成",
    "AuditLog / TechLog hybrid mirror 已完成",
    "DB_REPOSITORY_MODE=sqlite|hybrid|postgres 默认 sqlite",
    "下一步：ProjectionJob mirror，或前端系统状态页",
]


def p0_architecture_summary(ctx: UserContext) -> dict[str, Any]:
    query_plan = query_plan_for_context(ctx, table_alias="resource")
    return {"version": P0_ARCHITECTURE_VERSION, "title": "互联网大厂 SaaS P0 架构拆解", "runtimeMode": "audit_tech_hybrid_mirror", "currentContext": ctx.to_dict(), "mandatoryScopePlan": {"where": query_plan.where, "params": query_plan.params, "rule": query_plan.rule}, "taskPersistence": task_persistence_summary(), "layers": P0_LAYERS, "implementationSequence": IMPLEMENTATION_SEQUENCE, "definitionOfDone": ["业务查询按 tenant_id + deleted_at + Data Scope 过滤。", "任务、导入、队列、审计、日志可在 hybrid/postgres 模式 mirror。", "数据库迁移通过 Alembic 版本化执行。"]}
