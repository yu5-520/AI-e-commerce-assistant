# PostgreSQL / Alembic / Repository 过渡层

当前版本：V5.3.4。

本阶段新增 AuditLog / TechLog hybrid mirror：当前 SQLite Demo 写路径先成功，再按 `DB_REPOSITORY_MODE` 尝试镜像到 PostgreSQL Production Repository。

## 目标

```text
SQLite Demo Runtime
↓
继续承接当前导入、任务、证据、审计、删除记录测试
↓
Task / ImportJob / WorkerJob / AuditLog / TechLog 写路径
↓
PostgreSQL Production Mirror
↓
ProductionTaskRepository / ProductionImportJobRepository / ProductionWorkerJobRepository / ProductionAuditRepository / ProductionTechLogRepository
```

## 新增文件

```text
src/services/audit_tech_repository_mirror_service.py  AuditLog / TechLog mirror 服务
src/services/trace_audit_service.py                   AuditLog 写路径返回 productionMirror
src/services/tech_log_service.py                      TechLog 写路径返回 productionMirror
src/services/repository_runtime_service.py            auditTechHybridMirror 状态
src/db/repositories.py                                AuditLog / TechLog upsert
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
ProductionTaskRepository        decision_tasks list / get / upsert / soft_delete
ProductionImportJobRepository   import_jobs list / get / upsert
ProductionWorkerJobRepository   worker_jobs list / upsert by queue/status
ProductionAuditRepository       audit_logs trace timeline / upsert
ProductionTechLogRepository     tech_logs upsert
```

所有查询统一应用：

```text
tenant_id = current_tenant
org_id = current_org
deleted_at IS NULL
```

## 重要边界

1. 当前 Demo 服务仍先使用 SQLite runtime 表。
2. `hybrid` 模式会尝试 mirror，但 mirror 失败不会阻断 Demo。
3. `postgres` 模式目前还不是完全主写，只是启用 mirror，后续版本再提升 PostgreSQL 为主写路径。
4. ProjectionJob 还没有 mirror。

## 后续迁移顺序

```text
1. 使用 /api/system/repositories?check=true 检查连接
2. 验证 Task / ImportJob / WorkerJob / AuditLog / TechLog 的 productionMirror 字段
3. ProjectionJob mirror + DataVersion / AlertEvent 生产模型补齐
4. 前端系统状态页展示 DB / Repository / Worker / LLM / Audit 状态
```
