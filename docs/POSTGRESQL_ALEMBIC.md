# PostgreSQL / Alembic 生产数据模型骨架

当前版本：V5.3.0。

本阶段只新增生产数据库模型与迁移骨架，不替换当前 SQLite Demo 链路。

## 目标

```text
SQLite Demo Runtime
↓
保持现有报表导入、任务、证据、审计演示能力

PostgreSQL Production Target
↓
SQLAlchemy AsyncSession
Alembic migration
TenantScopedMixin
SoftDeleteMixin
TraceAuditMixin
ActorMixin
P0 production models
```

## 新增文件

```text
src/db/session.py                               Async SQLAlchemy engine / session factory
src/db/base.py                                  Declarative Base + Tenant / SoftDelete / Trace mixins
src/db/models.py                                P0 production model registry
alembic.ini                                     Alembic config
alembic/env.py                                  asyncpg migration env
alembic/script.py.mako                          migration template
alembic/versions/20260623_530_initial_p0_schema.py initial P0 schema scaffold
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

## 当前生产模型范围

```text
tenants
organizations
users
stores
import_jobs
projection_jobs
decision_tasks
task_events
task_evidence
worker_jobs
audit_logs
tech_logs
llm_gateway_events
```

## 重要边界

1. 当前 Demo 服务仍使用 SQLite runtime 表，不会因为新增 Alembic 自动迁移到 PostgreSQL。
2. 生产表统一使用 tenant_id / org_id / deleted_at / trace_id。
3. 生产删除默认软删除，Demo 删除仍可保留硬删除以方便测试。
4. WorkerJob 唯一幂等键使用 `(tenant_id, idempotency_key)`。
5. 下一步才应该做 Repository 生产实现，把 TaskRepository / ImportJobRepository 从 SQLite runtime 迁到 SQLAlchemy。

## 后续迁移顺序

```text
1. 确认 PostgreSQL 连接和 Alembic upgrade head 可运行
2. 为 UserContext 接入真实 JWT / Session
3. 为 TaskRepository 增加 SQLAlchemy 实现
4. 为 ImportJob / WorkerJob / AuditLog 增加 SQLAlchemy Repository
5. 保留 SQLite Demo fallback
6. 增加迁移测试和回滚检查
```
