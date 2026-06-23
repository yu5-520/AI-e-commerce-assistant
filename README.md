# AI ERP 经营单元电商协同系统 MVP

> 当前版本：V5.3.6。新增 DataVersion / AlertEvent 写路径 mirror：报表导入完成后，从导入结果中收集数据版本和预警事件，按 `DB_REPOSITORY_MODE` 尝试镜像到 PostgreSQL Repository。默认 `sqlite` 模式跳过 mirror，`hybrid/postgres` 模式启用 mirror；mirror 失败不影响当前 Demo。

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
DataVersion / AlertEvent：从导入结果收集并尝试 PostgreSQL mirror
↓
TraceId：贯穿 ImportJob / ProjectionJob / DataVersion / AlertEvent / WorkerJob / Task / Audit / TechLog
```

核心规则：**首页展示经营摘要，不展示工程代号；报表确认导入就是自动入库；商品、报表、总览必须随导入同步刷新；当前任务按优先级、截止时间和风险域排序；Demo 阶段可删除单条导入记录。**

## V5.3.6 新增

```text
src/services/data_alert_repository_mirror_service.py  DataVersion / AlertEvent mirror 服务
src/services/import_job_service.py                    ImportJob 完成后返回 productionMirror.dataAlert
src/services/repository_runtime_service.py            返回 dataAlertWriteMirror
src/services/p0_architecture_service.py               runtimeMode=data_alert_hybrid_mirror
```

## 当前真实状态

```text
已完成：TaskRepository / ImportJob / ProjectionJob / WorkerJob / AuditLog / TechLog SQLite-first PostgreSQL mirror。
已完成：DataVersion / AlertEvent 生产模型、迁移、写路径 mirror。
默认模式：DB_REPOSITORY_MODE=sqlite，mirror 跳过，Demo 稳定。
可测模式：DB_REPOSITORY_MODE=hybrid，写入后尝试 PostgreSQL mirror。
仍待完成：PostgreSQL 主写切换、生产 JWT / Session、前端系统状态页。
```

## 下一步

```text
A. V5.3.7：前端系统状态页，把 system / repository / architecture 状态可视化
B. V5.3.7：PostgreSQL 主写切换前检查清单
```
