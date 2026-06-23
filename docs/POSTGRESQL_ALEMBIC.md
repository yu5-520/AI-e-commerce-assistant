# PostgreSQL / Alembic / Repository 过渡层

当前版本：V5.3.1。

本阶段新增 SQLAlchemy Repository 过渡层，但默认不替换当前 SQLite Demo 链路。

## 目标

```text
SQLite Demo Runtime
↓
继续承接当前导入、任务、证据、审计、删除记录测试

PostgreSQL Production Target
↓
SQLAlchemy AsyncSession
Alembic migration
TenantScopedMixin
SoftDeleteMixin
TraceAuditMixin
Production Repositories
```

## 新增文件

```text
src/db/session.py                               Async SQLAlchemy engine / session factory
src/db/base.py                                  Declarative Base + Tenant / SoftDelete / Trace mixins
src/db/models.py                                P0 production model registry
src/db/repositories.py                          SQLAlchemy Repository 过渡层
src/services/repository_runtime_service.py      DB_REPOSITORY_MODE 与 health check
alembic.ini                                     Alembic config
alembic/env.py                                  asyncpg migration env
alembic/script.py.mako                          migration template
alembic/versions/20260623_530_initial_p0_schema.py initial P0 schema scaffold
```

## 运行模式

```text
DB_REPOSITORY_MODE=sqlite    默认模式：所有现有路由继续走 SQLite Demo
DB_REPOSITORY_MODE=hybrid    过渡模式：允许检查 PostgreSQL Repository，同时保留 SQLite fallback
DB_REPOSITORY_MODE=postgres  未来生产模式：逐步切换到 SQLAlchemy Repository
```

检查接口：

```text
GET /api/system/repositories
GET /api/system/repositories?check=true
```

## 迁移命令

```bash
export DATABASE_URL=postgresql+asyncpg://user:password@127.0.0.1:5432/ai_ecommerce
alembic upgrade head
```

生成新迁移：

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## 当前 Production Repository 范围

```text
ProductionTaskRepository        decision_tasks list / get / upsert / soft_delete
ProductionImportJobRepository   import_jobs list / get
ProductionWorkerJobRepository   worker_jobs list by queue/status
ProductionAuditRepository       audit_logs trace timeline
```

所有查询统一应用：

```text
tenant_id = current_tenant
org_id = current_org
deleted_at IS NULL
```

## 重要边界

1. 当前 Demo 服务仍使用 SQLite runtime 表，不会因为新增 Repository 自动迁移到 PostgreSQL。
2. 生产表统一使用 tenant_id / org_id / deleted_at / trace_id。
3. `hybrid` 模式用于验证 PostgreSQL Repository，不代表正式切换。
4. 下一步才应该做任务写路径 hybrid 双写。

## 后续迁移顺序

```text
1. 确认 PostgreSQL 连接和 alembic upgrade head 可运行
2. 使用 /api/system/repositories?check=true 检查连接
3. TaskRepository 写路径增加 hybrid 双写
4. ImportJob / WorkerJob / AuditLog 写路径逐步双写
5. 前端系统状态页展示 DB / Repository / Worker / LLM / Audit 状态
```
