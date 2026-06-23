# PostgreSQL / Alembic / Repository 过渡层

当前版本：V5.3.6。

本阶段新增 DataVersion / AlertEvent 写路径 mirror：报表导入完成后，从导入结果中收集数据版本和预警事件，按 `DB_REPOSITORY_MODE` 尝试镜像到 PostgreSQL Production Repository。

## 目标

```text
SQLite Demo Runtime
↓
继续承接当前导入、任务、证据、审计、删除记录测试
↓
Task / ImportJob / ProjectionJob / DataVersion / AlertEvent / WorkerJob / AuditLog / TechLog 写路径
↓
PostgreSQL Production Mirror
↓
Production Repositories
```

## 新增文件

```text
src/services/data_alert_repository_mirror_service.py  DataVersion / AlertEvent mirror 服务
src/services/import_job_service.py                    ImportJob 完成后返回 productionMirror.dataAlert
src/services/repository_runtime_service.py            dataAlertWriteMirror 状态
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
3. DataVersion / AlertEvent 从导入结果中收集，兼容单报表结果和批量 `results[]`。
4. `postgres` 模式目前还不是完全主写，只是启用 mirror，后续版本再提升 PostgreSQL 为主写路径。

## 后续迁移顺序

```text
1. 使用 /api/system/repositories?check=true 检查连接
2. 验证 Task / ImportJob / ProjectionJob / DataVersion / AlertEvent / WorkerJob / AuditLog / TechLog 的 productionMirror 字段
3. 前端系统状态页展示 DB / Repository / Worker / LLM / Audit 状态
4. PostgreSQL 主写切换前检查清单
```
