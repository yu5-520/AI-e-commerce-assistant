# AI ERP 经营单元电商协同系统 MVP

> 当前版本：V5.3.0。新增 PostgreSQL / Alembic 生产数据模型骨架：`src/db/session.py`、`src/db/base.py`、`src/db/models.py`、`alembic.ini`、`alembic/env.py`、初始 P0 schema migration 和 `docs/POSTGRESQL_ALEMBIC.md`。当前不替换 SQLite Demo 运行链路。

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
SQLite Demo Runtime：ImportJob / WorkerJob / Task / Evidence / Audit / LLM Gateway 继续可运行
↓
PostgreSQL Production Target：SQLAlchemy AsyncSession + Alembic + TenantScopedMixin + SoftDeleteMixin + TraceAuditMixin
↓
TraceId：贯穿 ImportJob / ProjectionJob / WorkerJob / WorkerTaskResult / Task / Evidence / RAG Staging / AuditLog / TechLog / LLM Gateway
↓
ModuleProjection / DashboardSummary / AlertEvent / Module Agent / DecisionTaskDraft
```

核心规则：**首页展示经营摘要，不展示工程代号；报表确认导入就是自动入库；商品、报表、总览必须随导入同步刷新；当前任务按优先级、截止时间和风险域排序；Demo 阶段可删除单条导入记录。**

## V5.3.0 新增

```text
src/db/session.py                               Async SQLAlchemy engine / session factory
src/db/base.py                                  Declarative Base + Timestamp / Tenant / SoftDelete / Trace / Actor mixins
src/db/models.py                                P0 production model registry
alembic.ini                                     Alembic config，DATABASE_URL 可覆盖
alembic/env.py                                  asyncpg migration env
alembic/script.py.mako                          migration template
alembic/versions/20260623_530_initial_p0_schema.py initial P0 schema scaffold
docs/POSTGRESQL_ALEMBIC.md                     PostgreSQL / Alembic 迁移说明
```

## 生产模型范围

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

## 常用接口

```text
GET    /api/health
GET    /api/system/db-status
GET    /api/system/security
GET    /api/architecture/p0
GET    /api/llm/status
GET    /api/llm/gateway
POST   /api/llm/generate
GET    /api/audit/traces/{trace_id}
GET    /api/audit/tech-logs
GET    /api/audit/tech-logs/summary
POST   /api/audit/tech-logs/test-redaction
GET    /api/worker/jobs/runtime
GET    /api/worker/jobs/results
GET    /api/worker/jobs/results?trace_id=<TRACE_ID>
GET    /api/worker/jobs/summary
POST   /api/data/import-jobs/confirm
POST   /api/data/import-jobs/report
POST   /api/data/import-jobs/mock-alerts
POST   /api/data/import-jobs/worker/execute-next
POST   /api/modules/todo/{task_id}/submit-evidence
POST   /api/modules/todo/{task_id}/review-evidence
POST   /api/system/reset-runtime-data?confirm=true
```

## Alembic 迁移命令

```bash
export DATABASE_URL=postgresql+asyncpg://user:password@127.0.0.1:5432/ai_ecommerce
alembic upgrade head
```

生成新迁移：

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## Worker 启动方式

```bash
# Demo 默认：不配置 Redis，API 使用 SQLite worker_jobs fallback
export WORKER_RUNTIME=sqlite

# Redis / ARQ 模式
export WORKER_RUNTIME=arq
export REDIS_URL=redis://127.0.0.1:6379/0
arq src.workers.arq_worker.WorkerSettings
```

## Nginx 部署入口

```bash
sudo cp deploy/nginx/ai-erp.conf /etc/nginx/conf.d/ai-erp.conf
sudo nginx -t
sudo systemctl reload nginx
```

## P0 下一步实施顺序

```text
1. 已完成：Async SQLAlchemy / Alembic / TenantScopedMixin / SoftDeleteMixin
2. 已完成：生产模型 Tenant / User / Store / ImportJob / Task / Worker / Audit / TechLog / LLMGatewayEvent
3. 下一步：SQLAlchemy Repository 逐步替换 SQLite Runtime Repository
4. UserContext：从 Demo Header 过渡到 JWT / Session
5. TaskRepository 生产实现：decision_tasks / task_events / task_evidence
6. ImportJob 生产实现：import_jobs / projection_jobs / data_version / imported_rows
7. WorkerJob 生产实现：worker_jobs 幂等、重试、认领
8. Audit / TechLog 生产实现：audit_logs / tech_logs / trace_id
9. 前端系统状态页：展示 /api/system/security、/api/architecture/p0、/api/llm/gateway
```

## 当前真实状态

```text
已完成：PostgreSQL / Alembic 生产数据模型骨架。
仍待完成：真实 PostgreSQL 实例、alembic upgrade head 实机执行、SQLAlchemy Repository 替换 SQLite Demo Repository、生产 JWT / Session。
保留不变：当前 SQLite Demo 运行链路、导入测试、任务测试、删除记录测试。
```
