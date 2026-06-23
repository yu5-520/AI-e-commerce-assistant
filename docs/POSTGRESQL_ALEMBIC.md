# PostgreSQL / Alembic / Repository 过渡层

当前版本：V5.3.5。

本阶段新增 ProjectionJob hybrid mirror，并补齐 DataVersion / AlertEvent 生产模型与迁移。

## 目标

```text
SQLite Demo Runtime
↓
继续承接当前导入、任务、证据、审计、删除记录测试
↓
Task / ImportJob / ProjectionJob / WorkerJob / AuditLog / TechLog 写路径
↓
PostgreSQL Production Mirror
↓
ProductionTaskRepository / ProductionImportJobRepository / ProductionProjectionJobRepository / ProductionWorkerJobRepository / ProductionAuditRepository / ProductionTechLogRepository
```

## 新增文件

```text
src/db/projection_repositories.py                  ProjectionJob / DataVersion / AlertEvent Repository
src/services/projection_repository_mirror_service.py ProjectionJob mirror 服务
src/db/models.py                                   DataVersion / AlertEvent 模型
alembic/versions/20260623_535_data_version_alert_event.py 增量迁移
src/services/import_job_service.py                 ProjectionJob 写路径返回 productionMirror
src/services/repository_runtime_service.py         projectionDataHybridMirror 状态
```

## 运行模式

```text
DB_REPOSITORY_MODE=sqlite    默认：只写 SQLite Demo，mirror skipped
DB_REPOSITORY_MODE=hybrid    过渡：SQLite 成功后尝试 PostgreSQL mirror，失败不影响 Demo
DB_REPOSITORY_MODE=postgres  未来：当前仍 SQLite-first，后续再提升 PostgreSQL 为主写路径
```

检查接口：

```text
GET /api/system/repositories
GET /api/system/repositories?check=true
```

## 当前 Production Repository 范围

```text
ProductionTaskRepository           decision_tasks list / get / upsert / soft_delete
ProductionImportJobRepository      import_jobs list / get / upsert
ProductionProjectionJobRepository  projection_jobs list / upsert
ProductionDataVersionRepository    data_versions upsert
ProductionAlertEventRepository     alert_events upsert
ProductionWorkerJobRepository      worker_jobs list / upsert by queue/status
ProductionAuditRepository          audit_logs trace timeline / upsert
ProductionTechLogRepository        tech_logs upsert
```

## 重要边界

1. 当前 Demo 服务仍先使用 SQLite runtime 表。
2. `hybrid` 模式会尝试 mirror，但 mirror 失败不会阻断 Demo。
3. DataVersion / AlertEvent 当前已建模，写路径 mirror 留到下一轮。
4. `postgres` 模式目前还不是完全主写，只是启用 mirror，后续版本再提升 PostgreSQL 为主写路径。

## 后续迁移顺序

```text
1. 使用 /api/system/repositories?check=true 检查连接
2. 验证 Task / ImportJob / ProjectionJob / WorkerJob / AuditLog / TechLog 的 productionMirror 字段
3. DataVersion / AlertEvent 写路径 mirror
4. 前端系统状态页展示 DB / Repository / Worker / LLM / Audit 状态
```
