# AI ERP 经营单元电商协同系统 MVP

> 当前版本：V5.3.3。新增 ImportJob / WorkerJob hybrid mirror：导入任务和后台队列任务先写 SQLite Demo 成功，再按 `DB_REPOSITORY_MODE` 尝试镜像到 PostgreSQL Repository。默认 `sqlite` 模式跳过 mirror，`hybrid/postgres` 模式启用 mirror；mirror 失败不影响当前 Demo。

## 当前主链路

```text
Browser / Client
↓
Nginx / FastAPI
↓
UserContext：tenant / org / user / role / store scope
↓
Repository Runtime：DB_REPOSITORY_MODE=sqlite | hybrid | postgres
↓
SQLite Demo Runtime：Task / ImportJob / WorkerJob 先成功
↓
PostgreSQL Mirror：hybrid/postgres 模式尝试写入 Production Repository
↓
TraceId：贯穿 ImportJob / WorkerJob / Task / Evidence / Audit / TechLog / LLM Gateway
↓
ModuleProjection / DashboardSummary / AlertEvent / Module Agent / DecisionTaskDraft
```

核心规则：**首页展示经营摘要，不展示工程代号；报表确认导入就是自动入库；商品、报表、总览必须随导入同步刷新；当前任务按优先级、截止时间和风险域排序；Demo 阶段可删除单条导入记录。**

## V5.3.3 新增

```text
src/services/import_worker_repository_mirror_service.py  ImportJob / WorkerJob mirror 服务
src/services/import_job_service.py                       ImportJob create / complete / fail 返回 productionMirror
src/services/worker_queue_service.py                     WorkerJob enqueue / claim / complete / fail / retry 返回 productionMirror
src/services/import_job_worker_service.py                 enqueue / execute-next 透出 mirror 状态
src/services/repository_runtime_service.py                返回 importWorkerHybridMirror
```

## Hybrid mirror 行为

```text
DB_REPOSITORY_MODE=sqlite
写入 SQLite Demo，productionMirror.status=skipped

DB_REPOSITORY_MODE=hybrid
SQLite 成功后尝试 PostgreSQL mirror；失败只返回 failed，不影响 Demo

DB_REPOSITORY_MODE=postgres
当前仍是 SQLite-first + mirror；后续版本再把 PostgreSQL 提升为主写路径
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
POST   /api/data/import-jobs/confirm
POST   /api/data/import-jobs/worker/execute-next
GET    /api/worker/jobs
POST   /api/worker/jobs/enqueue
POST   /api/worker/jobs/{worker_job_id}/complete
POST   /api/architecture/tasks/repository/create
POST   /api/architecture/tasks/repository/{task_id}/transition/{action}
POST   /api/architecture/tasks/repository/reset
```

## 当前真实状态

```text
已完成：TaskRepository / ImportJob / WorkerJob SQLite-first PostgreSQL mirror。
默认模式：DB_REPOSITORY_MODE=sqlite，mirror 跳过，Demo 稳定。
可测模式：DB_REPOSITORY_MODE=hybrid，写入后尝试 PostgreSQL mirror。
仍待完成：AuditLog / TechLog 写路径 hybrid mirror、PostgreSQL 主写切换、生产 JWT / Session。
```

## 下一步

```text
A. V5.3.4：AuditLog / TechLog 写路径 hybrid mirror
B. V5.3.4：前端系统状态页，把 system / repository / architecture 状态可视化
```
