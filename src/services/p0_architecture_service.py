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

P0_ARCHITECTURE_VERSION = "5.2.0"


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
        "status": "planned",
        "target": "所有核心表默认 deleted_at IS NULL；生产删除只软删除，Demo 可硬删。",
        "currentGap": "导入记录删除链路仍偏 Demo hard delete，需要生产模式软删除策略。",
        "mustNot": ["生产环境物理删除业务记录", "唯一索引忽略 deleted_at"],
    },
    {
        "id": "P0-3",
        "name": "任务系统持久化与状态机",
        "status": "evidence_audit_persistence",
        "target": "tasks/task_events/task_logs/task_evidence 落库，状态变更与事件同事务。",
        "currentGap": "Agent 入池、待办生命周期、报表导入前端同步、创意 Agent 入池已接入 TaskRepository；证据提交和复核已写入 task_evidence / task_logs。",
        "mustNot": ["非法状态跃迁", "任务状态更新成功但审计事件丢失"],
    },
    {
        "id": "P0-4",
        "name": "报表导入事务链与 ImportJob",
        "status": "import_job_scaffolded",
        "target": "ImportJob -> DataVersion -> ImportedRows -> ProjectionJob -> AlertEvent -> TaskDraft -> AuditLog。",
        "currentGap": "已新增 import_jobs / projection_jobs 和 /api/data/import-jobs/* 包装接口；前端导入确认优先走 ImportJob，失败再回退旧导入。下一步把导入、投影、预警拆到 Worker / Redis。",
        "mustNot": ["导入接口长时间阻塞", "重复执行生成重复任务"],
    },
    {
        "id": "P0-5",
        "name": "PostgreSQL 生产数据模型",
        "status": "planned",
        "target": "SQLite 仅 Demo；生产使用 PostgreSQL + async SQLAlchemy + Alembic。",
        "currentGap": "当前依赖仍以轻量 Demo 为主，需要生产依赖和迁移层。",
        "mustNot": ["生产环境使用 SQLite", "无索引支撑待办/数据版本查询"],
    },
    {
        "id": "P0-6",
        "name": "Worker / Redis 后台任务",
        "status": "worker_queue_scaffolded",
        "target": "导入、投影、预警、Agent 分析进入后台队列，任务幂等可重试。",
        "currentGap": "已新增 worker_jobs 队列表、幂等 key、优先级、认领、完成、失败、重试 API；仍需接入 Redis / ARQ 并将 ImportJob 真正异步执行。",
        "mustNot": ["大报表阻塞 FastAPI 事件循环", "Worker 重试产生副作用"],
    },
    {
        "id": "P0-7",
        "name": "LLM Gateway 熔断降级与配额",
        "status": "partial",
        "target": "熔断、限流、租户配额、结果缓存、Schema 校验、规则模板降级。",
        "currentGap": "已有 LLM 边界与 fallback，但缺少生产级熔断和租户级配额。",
        "mustNot": ["LLM 不可用导致核心链路中断", "AI 输出绕过 Schema 写业务库"],
    },
    {
        "id": "P0-8",
        "name": "Audit / Logs 双层体系",
        "status": "partial",
        "target": "AuditLog 存业务审计，TechLog 输出 JSON，两者通过 trace_id 关联。",
        "currentGap": "task_evidence / task_logs 已承接证据提交和复核审计；ImportJob / ProjectionJob / WorkerJob 已有运行记录；仍需全链路 trace_id 与独立 audit_logs 表。",
        "mustNot": ["日志输出明文 Token/密码", "业务审计与技术日志混在一起"],
    },
    {
        "id": "P0-9",
        "name": "Nginx 前后端分离部署",
        "status": "planned",
        "target": "Nginx 服务静态前端，/api 反代 FastAPI，HTTPS/CORS/限流/安全头统一配置。",
        "currentGap": "当前 FastAPI 仍直接挂载 web_demo 静态目录。",
        "mustNot": ["生产用 FastAPI 直接托管全部前端资源", "CORS 全开放"],
    },
]


IMPLEMENTATION_SEQUENCE = [
    "数据库基础层：Async SQLAlchemy / Alembic / TenantScopedMixin / SoftDeleteMixin",
    "UserContext：JWT/Session 解析 tenant_id、user_id、role、store scope",
    "ScopedRepository：统一注入 tenant、store、deleted_at 过滤",
    "Task 持久化镜像：task_status、task_events、task_logs、task_evidence + 状态机约束",
    "TaskRepository Scoped Reads：通过 UserContext 读取可见任务并支持启动快照恢复",
    "TaskRepository 写路径过渡：新增 create / transition / reset 的 repository API",
    "正式任务 API 切换：Agent 入池、待办接收/提交/复核/完成/重置已接入 repository 写路径",
    "报表任务同步桥：新增 report_task_repository_sync_service 与 /api/data/report-tasks/sync-current",
    "前端导入确认自动同步：report-task-sync.js 包装 confirmReportImport / importMockAlerts",
    "创意 Agent 入池同步：creative_task_repository_sync_service 接入 TaskRepository",
    "证据提交审计入库：task_evidence_audit_service 写入 task_evidence / task_logs",
    "ImportJob 骨架：import_job_service /api/data/import-jobs/* import_jobs projection_jobs",
    "Worker Queue 骨架：worker_queue_service /api/worker/jobs/* worker_jobs 幂等重试",
    "Redis / ARQ 替换：把 SQLite 队列表切换为真正后台 Worker 执行",
    "LLM Gateway：熔断、限流、租户配额、Schema 校验、规则降级",
    "Audit/Logs：业务审计表 + JSON 技术日志 + trace_id",
    "Nginx：前后端分离、HTTPS、限流、安全头",
]


def p0_architecture_summary(ctx: UserContext) -> dict[str, Any]:
    query_plan = query_plan_for_context(ctx, table_alias="resource")
    return {
        "version": P0_ARCHITECTURE_VERSION,
        "title": "互联网大厂 SaaS P0 架构拆解",
        "runtimeMode": "worker_queue_scaffolded",
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
        ],
    }
