# AI ERP 经营单元电商协同系统 MVP

> 当前版本：V5.3.2。新增 TaskRepository hybrid mirror：任务创建、流转、重置先写 SQLite Demo 成功，再按 `DB_REPOSITORY_MODE` 尝试镜像到 PostgreSQL `ProductionTaskRepository`。默认 `sqlite` 模式跳过 mirror，`hybrid/postgres` 模式启用 mirror；mirror 失败不影响当前 Demo。

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
SQLite Demo Runtime：任务创建 / 流转 / 重置先成功
↓
PostgreSQL Mirror：hybrid/postgres 模式下尝试写入 ProductionTaskRepository
↓
TraceId：贯穿 ImportJob / ProjectionJob / WorkerJob / WorkerTaskResult / Task / Evidence / RAG Staging / AuditLog / TechLog / LLM Gateway
↓
ModuleProjection / DashboardSummary / AlertEvent / Module Agent / DecisionTaskDraft
```

核心规则：**首页展示经营摘要，不展示工程代号；报表确认导入就是自动入库；商品、报表、总览必须随导入同步刷新；当前任务按优先级、截止时间和风险域排序；Demo 阶段可删除单条导入记录。**

## V5.3.2 新增

```text
src/services/task_repository_mirror_service.py  TaskRepository PostgreSQL mirror 服务
src/services/task_repository_write_service.py   create / transition / reset 返回 productionMirror
src/services/repository_runtime_service.py      返回 taskHybridMirror 运行状态
GET /api/system/repositories                    可查看 activeMode 与 taskHybridMirror
```

## Task hybrid mirror 行为

```text
DB_REPOSITORY_MODE=sqlite
任务写入 SQLite Demo，productionMirror.status=skipped

DB_REPOSITORY_MODE=hybrid
任务写入 SQLite Demo，然后尝试 PostgreSQL mirror；失败只返回 mirror failed，不影响 Demo

DB_REPOSITORY_MODE=postgres
任务写入 SQLite Demo 后尝试 PostgreSQL mirror；后续版本再把 PostgreSQL 提升为主写路径
```

写路径响应会包含：

```text
productionMirror.status = skipped | mirrored | failed
productionMirror.mode = sqlite | hybrid | postgres
productionMirror.fallback = true | false
```

## 常用接口

```text
GET    /api/health
GET    /api/system/security
GET    /api/system/repositories
GET    /api/system/repositories?check=true
GET    /api/architecture/p0
POST   /api/architecture/tasks/repository/create
POST   /api/architecture/tasks/repository/{task_id}/transition/{action}
POST   /api/architecture/tasks/repository/reset
POST   /api/modules/todo/{task_id}/submit-evidence
POST   /api/system/reset-runtime-data?confirm=true
```

## 当前真实状态

```text
已完成：TaskRepository SQLite-first PostgreSQL mirror。
默认模式：DB_REPOSITORY_MODE=sqlite，mirror 跳过，Demo 稳定。
可测模式：DB_REPOSITORY_MODE=hybrid，任务写入后尝试 PostgreSQL mirror。
仍待完成：ImportJob / WorkerJob / AuditLog 写路径 hybrid 双写、真实 PostgreSQL 实例、生产 JWT / Session。
```

## 下一步

```text
A. V5.3.3：ImportJob / WorkerJob 写路径 hybrid 双写
B. V5.3.3：前端系统状态页，把 /api/system/security、/api/system/repositories、/api/architecture/p0 可视化
```
