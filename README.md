# AI ERP 经营单元电商协同系统 MVP

> 当前版本：V5.3.1。新增 SQLAlchemy Repository 过渡层：`src/db/repositories.py`、`src/services/repository_runtime_service.py`、`GET /api/system/repositories` 和 `DB_REPOSITORY_MODE=sqlite|hybrid|postgres`。当前默认仍是 SQLite Demo，PostgreSQL Repository 先进入可检查、可逐步迁移状态。

## 当前主链路

```text
Browser / Client
↓
Nginx：静态前端、/api 反代、粗限流、安全头、HTTPS 入口预留
↓
FastAPI：Security Headers + API RateLimit + CORS Allowlist
↓
UserContext：tenant / org / user / role / store scope
↓
Repository Runtime：DB_REPOSITORY_MODE=sqlite | hybrid | postgres
↓
SQLite Demo Runtime：继续承接现有 ImportJob / WorkerJob / Task / Evidence / Audit / LLM Gateway
↓
PostgreSQL Production Target：SQLAlchemy AsyncSession + Alembic + Production Repositories
↓
TraceId：贯穿 ImportJob / ProjectionJob / WorkerJob / WorkerTaskResult / Task / Evidence / RAG Staging / AuditLog / TechLog / LLM Gateway
↓
ModuleProjection / DashboardSummary / AlertEvent / Module Agent / DecisionTaskDraft
```

核心规则：**首页展示经营摘要，不展示工程代号；报表确认导入就是自动入库；商品、报表、总览必须随导入同步刷新；当前任务按优先级、截止时间和风险域排序；Demo 阶段可删除单条导入记录。**

## V5.3.1 新增

```text
src/db/repositories.py                         SQLAlchemy Repository 过渡层
src/services/repository_runtime_service.py     Repository Runtime 模式与 PostgreSQL health check
src/api/routes/system.py                       新增 GET /api/system/repositories
.env.example                                   新增 DB_REPOSITORY_MODE=sqlite|hybrid|postgres
```

## Repository 过渡层

```text
ProductionTaskRepository        list / get / upsert / soft_delete decision_tasks
ProductionImportJobRepository   list / get import_jobs
ProductionWorkerJobRepository   list worker_jobs by queue/status
ProductionAuditRepository       trace timeline from audit_logs
```

每个查询统一走：

```text
tenant_id = current_tenant
org_id = current_org
deleted_at IS NULL
```

## 运行模式

```text
DB_REPOSITORY_MODE=sqlite    默认模式，现有 Demo 稳定运行
DB_REPOSITORY_MODE=hybrid    用于测试 PostgreSQL Repository，同时保留 SQLite fallback
DB_REPOSITORY_MODE=postgres  未来生产切换模式
```

检查接口：

```text
GET /api/system/repositories
GET /api/system/repositories?check=true
```

## Alembic 迁移命令

```bash
export DATABASE_URL=postgresql+asyncpg://user:password@127.0.0.1:5432/ai_ecommerce
alembic upgrade head
```

## 常用接口

```text
GET    /api/health
GET    /api/system/db-status
GET    /api/system/security
GET    /api/system/repositories
GET    /api/system/repositories?check=true
GET    /api/architecture/p0
GET    /api/llm/status
GET    /api/llm/gateway
POST   /api/llm/generate
GET    /api/audit/traces/{trace_id}
GET    /api/worker/jobs/runtime
POST   /api/data/import-jobs/confirm
POST   /api/modules/todo/{task_id}/submit-evidence
POST   /api/system/reset-runtime-data?confirm=true
```

## 当前真实状态

```text
已完成：PostgreSQL / Alembic 生产模型、SQLAlchemy Repository 过渡层、Repository Runtime 状态接口。
仍待完成：真实 PostgreSQL 实例、alembic upgrade head 实机执行、hybrid 双写、生产 JWT / Session。
保留不变：当前 SQLite Demo 运行链路、导入测试、任务测试、删除记录测试。
```

## 下一步

```text
A. V5.3.2：TaskRepository hybrid 双写，把任务创建/流转同时写 SQLite 和 PostgreSQL
B. V5.3.2：前端系统状态页，把 /api/system/security、/api/system/repositories、/api/architecture/p0 可视化
```
