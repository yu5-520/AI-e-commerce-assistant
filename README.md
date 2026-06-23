# AI ERP 经营单元电商协同系统 MVP

> 当前版本：V5.3.5。新增 ProjectionJob hybrid mirror，并补齐 DataVersion / AlertEvent 生产模型与 Alembic 增量迁移。ProjectionJob 先写 SQLite Demo 成功，再按 `DB_REPOSITORY_MODE` 尝试镜像到 PostgreSQL Repository；mirror 失败不影响当前 Demo。

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
SQLite Demo Runtime：Task / ImportJob / ProjectionJob / WorkerJob / AuditLog / TechLog 先成功
↓
PostgreSQL Mirror：hybrid/postgres 模式尝试写入 Production Repository
↓
TraceId：贯穿 ImportJob / ProjectionJob / WorkerJob / Task / Evidence / Audit / TechLog / LLM Gateway
↓
DataVersion / AlertEvent：生产模型已补齐，下一步接写路径
```

核心规则：**首页展示经营摘要，不展示工程代号；报表确认导入就是自动入库；商品、报表、总览必须随导入同步刷新；当前任务按优先级、截止时间和风险域排序；Demo 阶段可删除单条导入记录。**

## V5.3.5 新增

```text
src/db/projection_repositories.py                  ProjectionJob / DataVersion / AlertEvent 生产 Repository
src/services/projection_repository_mirror_service.py ProjectionJob mirror 服务
src/db/models.py                                   新增 DataVersion / AlertEvent 模型
alembic/versions/20260623_535_data_version_alert_event.py 增量迁移
src/services/import_job_service.py                 ProjectionJob 返回 productionMirror
src/services/repository_runtime_service.py         返回 projectionDataHybridMirror
```

## 当前真实状态

```text
已完成：TaskRepository / ImportJob / ProjectionJob / WorkerJob / AuditLog / TechLog SQLite-first PostgreSQL mirror。
已完成：DataVersion / AlertEvent 生产模型和迁移。
默认模式：DB_REPOSITORY_MODE=sqlite，mirror 跳过，Demo 稳定。
可测模式：DB_REPOSITORY_MODE=hybrid，写入后尝试 PostgreSQL mirror。
仍待完成：DataVersion / AlertEvent 写路径 mirror、PostgreSQL 主写切换、生产 JWT / Session。
```

## 下一步

```text
A. V5.3.6：DataVersion / AlertEvent 写路径 mirror
B. V5.3.6：前端系统状态页，把 system / repository / architecture 状态可视化
```
