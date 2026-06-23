# AI ERP 经营单元电商协同系统 MVP

> 当前版本：V5.3.7。新增前端系统状态页：把 `/api/system/security`、`/api/system/repositories`、`/api/architecture/p0` 可视化，方便演示当前 SQLite-first / PostgreSQL mirror / P0 架构成熟度。

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
SQLite Demo Runtime：Task / ImportJob / ProjectionJob / WorkerJob / AuditLog / TechLog 先成功
↓
PostgreSQL Mirror：hybrid/postgres 模式尝试写入 Production Repository
↓
TraceId：贯穿 ImportJob / ProjectionJob / DataVersion / AlertEvent / WorkerJob / Task / Audit / TechLog
```

核心规则：**首页展示经营摘要，不展示工程代号；报表确认导入就是自动入库；商品、报表、总览必须随导入同步刷新；当前任务按优先级、截止时间和风险域排序；Demo 阶段可删除单条导入记录。**

## V5.3.7 新增

```text
web_demo/modules/system-status/page.js  系统状态页
web_demo/system-status.css              系统状态页样式
web_demo/index.html                     新增系统状态导航和脚本加载
web_demo/bootstrap.js                   注册 SystemStatusPage 并开放 owner / manager 可见
```

## 当前真实状态

```text
已完成：TaskRepository / ImportJob / ProjectionJob / DataVersion / AlertEvent / WorkerJob / AuditLog / TechLog SQLite-first PostgreSQL mirror。
已完成：前端系统状态页，可查看安全状态、Repository mirror、P0 架构层。
默认模式：DB_REPOSITORY_MODE=sqlite，mirror 跳过，Demo 稳定。
可测模式：DB_REPOSITORY_MODE=hybrid，写入后尝试 PostgreSQL mirror。
仍待完成：PostgreSQL 主写切换、生产 JWT / Session、mirror service 去重复。
```

## 下一步

```text
A. V5.3.8：repository_mirror_base_service 去重复
B. V5.3.8：PostgreSQL 主写切换前检查清单
```
