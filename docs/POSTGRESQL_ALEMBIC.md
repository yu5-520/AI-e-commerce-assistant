# PostgreSQL / Alembic / Repository 过渡层

当前版本：V5.3.9。

本阶段新增 PostgreSQL 主写切换前检查清单。该能力只做 readiness 评估，不会修改 `DB_REPOSITORY_MODE`，也不会切换写路径。

## 当前链路

```text
SQLite Demo Runtime
↓
核心写路径 SQLite-first
↓
repository_mirror_base_service
↓
PostgreSQL Mirror
↓
/api/system/postgres-cutover-check
↓
主写切换前检查项：连接、迁移、mirror、回退、身份、回滚
```

## 新增文件

```text
src/services/postgres_cutover_check_service.py  PostgreSQL 主写切换前检查服务
src/api/routes/system.py                        GET /api/system/postgres-cutover-check
web_demo/modules/system-status/page.js          前端展示 pass / warn / blocked
```

## 检查接口

```text
GET /api/system/repositories
GET /api/system/repositories?check=true
GET /api/system/postgres-cutover-check
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

## Cutover 检查项

```text
repository_mode
postgres_connection
alembic_files
mirror_base
production_models
demo_fallback
auth_boundary
rollback_plan
taskHybridMirror
importWorkerHybridMirror
auditTechHybridMirror
projectionDataHybridMirror
dataAlertWriteMirror
```

## 重要边界

1. 当前 Demo 服务仍先使用 SQLite runtime 表。
2. `hybrid` 模式会尝试 mirror，但 mirror 失败不会阻断 Demo。
3. `postgres` 模式目前还不是完全主写，只是 readiness 目标状态。
4. 主写切换前必须先看 `/api/system/postgres-cutover-check` 的 blocked 项。

## 后续迁移顺序

```text
1. DB_REPOSITORY_MODE=hybrid
2. /api/system/postgres-cutover-check 消除 blocked
3. 核心链路抽样对账
4. 写入 rollback runbook
5. 再考虑 postgres 主写切换
```
