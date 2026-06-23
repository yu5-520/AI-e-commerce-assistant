# AI ERP 经营单元电商协同系统 MVP

> 当前版本：V5.3.4。新增 AuditLog / TechLog hybrid mirror：业务审计和技术日志先写 SQLite Demo 成功，再按 `DB_REPOSITORY_MODE` 尝试镜像到 PostgreSQL Repository。默认 `sqlite` 模式跳过 mirror，`hybrid/postgres` 模式启用 mirror；mirror 失败不影响当前 Demo。

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
SQLite Demo Runtime：Task / ImportJob / WorkerJob / AuditLog / TechLog 先成功
↓
PostgreSQL Mirror：hybrid/postgres 模式尝试写入 Production Repository
↓
TraceId：贯穿 ImportJob / WorkerJob / Task / Evidence / Audit / TechLog / LLM Gateway
↓
ModuleProjection / DashboardSummary / AlertEvent / Module Agent / DecisionTaskDraft
```

核心规则：**首页展示经营摘要，不展示工程代号；报表确认导入就是自动入库；商品、报表、总览必须随导入同步刷新；当前任务按优先级、截止时间和风险域排序；Demo 阶段可删除单条导入记录。**

## V5.3.4 新增

```text
src/services/audit_tech_repository_mirror_service.py  AuditLog / TechLog mirror 服务
src/services/trace_audit_service.py                   write_audit_log 返回 productionMirror
src/services/tech_log_service.py                      write_tech_log 返回 productionMirror
src/db/repositories.py                                ProductionAuditRepository / ProductionTechLogRepository upsert
src/services/repository_runtime_service.py            返回 auditTechHybridMirror
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

## 当前真实状态

```text
已完成：TaskRepository / ImportJob / WorkerJob / AuditLog / TechLog SQLite-first PostgreSQL mirror。
默认模式：DB_REPOSITORY_MODE=sqlite，mirror 跳过，Demo 稳定。
可测模式：DB_REPOSITORY_MODE=hybrid，写入后尝试 PostgreSQL mirror。
仍待完成：ProjectionJob mirror、PostgreSQL 主写切换、生产 JWT / Session。
```

## 下一步

```text
A. V5.3.5：ProjectionJob mirror + DataVersion / AlertEvent 生产模型补齐
B. V5.3.5：前端系统状态页，把 system / repository / architecture 状态可视化
```
