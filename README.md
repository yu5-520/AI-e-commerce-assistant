# AI ERP 经营单元电商协同系统 MVP

> 当前版本：V5.3.8。新增 `repository_mirror_base_service`：把各 mirror service 重复的 mode 判断、skipped、failed、event-loop guard 和 summary 结构统一到公共层，业务 mirror 只保留各自 Repository 适配。

## 当前主链路

```text
Browser / Client
↓
Nginx / FastAPI
↓
系统状态页：system / repository / architecture 三类状态
↓
Repository Runtime：DB_REPOSITORY_MODE=sqlite | hybrid | postgres
↓
repository_mirror_base_service：统一 mirror 控制流
↓
SQLite Demo Runtime：Task / ImportJob / ProjectionJob / WorkerJob / AuditLog / TechLog 先成功
↓
PostgreSQL Mirror：hybrid/postgres 模式尝试写入 Production Repository
↓
TraceId：贯穿 ImportJob / ProjectionJob / DataVersion / AlertEvent / WorkerJob / Task / Audit / TechLog
```

核心规则：**首页展示经营摘要，不展示工程代号；报表确认导入就是自动入库；商品、报表、总览必须随导入同步刷新；当前任务按优先级、截止时间和风险域排序；Demo 阶段可删除单条导入记录。**

## V5.3.8 新增

```text
src/services/repository_mirror_base_service.py  Mirror 公共控制层
src/services/task_repository_mirror_service.py  使用 base service
src/services/import_worker_repository_mirror_service.py 使用 base service
src/services/audit_tech_repository_mirror_service.py 使用 base service
src/services/projection_repository_mirror_service.py 使用 base service
src/services/data_alert_repository_mirror_service.py 使用 base service
src/services/repository_runtime_service.py      返回 mirrorBase 状态
```

## 当前真实状态

```text
已完成：TaskRepository / ImportJob / ProjectionJob / DataVersion / AlertEvent / WorkerJob / AuditLog / TechLog SQLite-first PostgreSQL mirror。
已完成：前端系统状态页，可查看安全状态、Repository mirror、P0 架构层。
已完成：mirror 公共控制层，降低重复代码。
默认模式：DB_REPOSITORY_MODE=sqlite，mirror 跳过，Demo 稳定。
可测模式：DB_REPOSITORY_MODE=hybrid，写入后尝试 PostgreSQL mirror。
仍待完成：PostgreSQL 主写切换、生产 JWT / Session、README / docs 进一步拆分。
```

## 下一步

```text
A. V5.3.9：PostgreSQL 主写切换前检查清单
B. V5.3.9：README / docs / CHANGELOG 拆分，降低文档重复
```
