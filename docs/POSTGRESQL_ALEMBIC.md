# PostgreSQL / Alembic / Repository 迁移说明

> 当前版本：V5.4.0。本文件只记录数据库模型、迁移、Repository 范围和主写切换前检查。版本流水账请看 `docs/CHANGELOG.md`。

## 运行模式

```text
DB_REPOSITORY_MODE=sqlite    默认：只写 SQLite Demo，mirror skipped
DB_REPOSITORY_MODE=hybrid    过渡：SQLite 成功后尝试 PostgreSQL mirror，失败不影响 Demo
DB_REPOSITORY_MODE=postgres  目标：未来主写模式，当前仍需 cutover check 通过后再进入
```

## 迁移文件

```text
alembic/versions/20260623_530_initial_p0_schema.py
alembic/versions/20260623_535_data_version_alert_event.py
```

## Production Repository 范围

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

## 检查接口

```text
GET /api/system/repositories
GET /api/system/repositories?check=true
GET /api/system/postgres-cutover-check
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

## 主写切换顺序

```text
1. 保持 DB_REPOSITORY_MODE=sqlite，保证 Demo 稳定
2. 配置 DATABASE_URL
3. 执行 Alembic 迁移
4. 切 DB_REPOSITORY_MODE=hybrid
5. 查看 /api/system/postgres-cutover-check
6. 消除 blocked 项
7. 做核心链路抽样对账
8. 写入 rollback runbook
9. 再考虑 DB_REPOSITORY_MODE=postgres
```

## 边界

- 当前 Demo 服务仍先使用 SQLite runtime 表。
- `hybrid` 模式会尝试 mirror，但 mirror 失败不会阻断 Demo。
- `postgres` 模式目前仍是目标状态，不应绕过 cutover check 直接切换。
- 生产身份体系、JWT / Session、权限审计仍需后续接入。
