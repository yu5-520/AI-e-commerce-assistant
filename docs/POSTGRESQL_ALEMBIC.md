# PostgreSQL / Alembic / Repository 过渡层

当前版本：V5.3.8。

本阶段新增 `repository_mirror_base_service`：统一 SQLite-first PostgreSQL mirror 的控制流，业务服务只保留各自 Production Repository 适配。

## 目标

```text
SQLite Demo Runtime
↓
Task / ImportJob / ProjectionJob / DataVersion / AlertEvent / WorkerJob / AuditLog / TechLog 写路径
↓
repository_mirror_base_service
↓
PostgreSQL Production Mirror
↓
Production Repositories
```

## 新增文件

```text
src/services/repository_mirror_base_service.py  Mirror 公共控制层
src/services/repository_runtime_service.py      mirrorBase 状态
```

## 已接入 base 的 mirror service

```text
src/services/task_repository_mirror_service.py
src/services/import_worker_repository_mirror_service.py
src/services/audit_tech_repository_mirror_service.py
src/services/projection_repository_mirror_service.py
src/services/data_alert_repository_mirror_service.py
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
3. mirror 控制流已经统一到 `repository_mirror_base_service`。
4. `postgres` 模式目前还不是完全主写，只是启用 mirror，后续版本再提升 PostgreSQL 为主写路径。

## 后续迁移顺序

```text
1. 使用 /api/system/repositories?check=true 检查连接
2. 验证 productionMirror 字段和 mirrorBase 状态
3. PostgreSQL 主写切换前检查清单
4. README / docs / CHANGELOG 拆分，降低文档重复
```
