# AI ERP 经营单元电商协同系统 MVP

> 当前版本：V5.1.9。新增 ImportJob 骨架：报表导入新增 `import_jobs` / `projection_jobs` 运行记录和 `/api/data/import-jobs/*` 包装接口；前端确认导入优先走 ImportJob，失败再回退旧导入链路。

## 当前主链路

```text
报表模块导入数据表
↓
字段映射 / 数据校验 / 店铺归属 / 账号权限切片
↓
确认导入后自动入库
↓
ImportJob：记录导入请求、结果、异常和数据版本
↓
DataVersion 数据版本进入后端追溯
↓
完整导入行持久化 imported_report_rows
↓
ProjectionJob：记录模块投影刷新和任务同步结果
↓
ModuleProjection：刷新商品、流量、报表、首页、经营单元摘要
↓
DashboardSummary：最新导入 / 报表记录 / 商品数量 / 任务队列
↓
AlertEvent：系统规则生成预警事件
↓
模块 Agent：基于 ModuleProjection 生成只读证据和问题判断
↓
DecisionTaskDraft：补充信息 / 经营路径 / 行动顺序
↓
任务默认进入处理中，待办页提交执行证据和成果
↓
总管复核 / 下一轮数据复盘路径效果
↓
RAG Memory：复核后入库并在下一轮召回
```

Demo 清理链路：**导入记录删除 → 清除该版本 imported_report_rows / data_snapshots / metric_snapshots / alert_events / rollback 记录 → 关联活跃任务归档 → 报表、总览、商品、待办刷新。**

核心规则：**首页展示经营摘要，不展示工程代号；报表确认导入就是自动入库；商品、报表、总览必须随导入同步刷新；当前任务按优先级、截止时间和风险域排序；Demo 阶段可删除单条导入记录。**

## V5.1.x P0 SaaS 架构新增

```text
src/core/context.py                            UserContext：tenant / user / role / store scope 统一注入
src/repositories/scoped_repository.py          ScopedRepository：tenant_id / deleted_at / Data Scope 查询约束
src/repositories/task_repository.py            TaskRepository：基于 UserContext 的任务持久化读写封装
src/services/task_repository_write_service.py  TaskRepository 写路径过渡服务：create / transition / reset
src/services/report_task_repository_sync_service.py 报表预警任务同步桥
src/api/routes/report_task_sync.py             /api/data/report-tasks/sync-current
web_demo/core/report-task-sync.js              报表导入优先走 ImportJob，失败回退旧链路
src/services/creative_task_repository_sync_service.py 创意 Agent 入池同步桥
src/services/task_evidence_audit_service.py    证据提交 / 复核写入 task_evidence 与 task_logs
src/services/import_job_service.py             ImportJob / ProjectionJob 运行记录服务
src/api/routes/import_jobs.py                  /api/data/import-jobs/*
src/services/p0_architecture_service.py        P0 SaaS 架构拆解运行态摘要
src/services/task_state_machine_service.py     P0 任务状态机与 SQLite 持久化镜像
src/api/routes/modules/agents.py               Agent / 创意 Agent 入池接口已接入 TaskRepository 写路径
src/api/routes/modules/todo.py                 待办接收 / 提交 / 复核 / 完成 / 重置已接入 TaskRepository 写路径
src/api/routes/architecture.py                 /api/architecture/p0 与 /api/architecture/context
src/api/routes/task_persistence.py             /api/architecture/tasks/persistence、repository、create、transition、reset 与 sync-runtime
docs/P0_SAAS_ARCHITECTURE.md                   互联网大厂 SaaS P0 架构说明
requirements.txt                               补充 SQLAlchemy / asyncpg / Alembic / Redis / ARQ 等生产依赖
```

P0 升级目标：

```text
FastAPI 模块化单体
+ UserContext 依赖注入
+ ScopedRepository 强制过滤
+ PostgreSQL 生产数据模型
+ 持久化任务状态机
+ ImportJob 事务链
+ Redis / Worker 异步任务
+ LLM Gateway 熔断降级
+ AuditLog / JSON TechLog
+ Nginx 前后端分离
```

当前 P0 进度：**任务系统已具备 SQLite mirror、TaskRepository scoped reads、启动快照恢复、写路径过渡 API，并已接入 Agent 入池、待办核心生命周期动作、报表导入前端同步、创意 Agent 入池和证据提交审计入库。报表导入已新增 ImportJob / ProjectionJob 运行记录和前端优先调用链。下一步是 Worker / Redis 异步化。**

## 关键目录

```text
src/api/main.py                                 FastAPI 入口，版本 5.1.9
src/core/context.py                             SaaS UserContext 依赖注入骨架
src/repositories/scoped_repository.py           多租户 / 软删除 / 数据范围统一查询约束
src/repositories/task_repository.py             任务 Repository：按 tenant / store / deleted_at 过滤读取与 upsert
src/services/task_repository_write_service.py   任务 Repository 写路径过渡服务
src/services/report_task_repository_sync_service.py 报表任务同步到 Repository
src/api/routes/report_task_sync.py              报表任务同步 API
web_demo/core/report-task-sync.js               前端报表导入 ImportJob 补丁
src/services/creative_task_repository_sync_service.py 创意任务同步到 Repository
src/services/creative_vertical_agent_service.py 创意 Agent 分析与测试包生成；仍不直接发布商品
src/services/task_evidence_audit_service.py     证据提交 / 复核审计持久化
src/services/task_evidence_service.py           待办执行证据提交与复核
src/services/import_job_service.py              ImportJob / ProjectionJob 服务
src/api/routes/import_jobs.py                   ImportJob API
src/services/task_state_machine_service.py      任务状态机 / 持久化镜像 / task_events / task_logs / task_evidence
src/services/p0_architecture_service.py         P0 架构摘要服务
src/api/routes/modules/agents.py                Agent 与创意 Agent 入池任务持久化入口
src/api/routes/modules/todo.py                  待办生命周期持久化入口
src/api/routes/architecture.py                  P0 架构可视化 API
src/api/routes/task_persistence.py              任务持久化镜像状态、Repository 读写与同步 API
src/services/data_version_service.py            数据版本回滚 / Demo 删除
src/api/routes/data_import.py                   旧报表导入接口；当前作为 ImportJob 回退链路
src/services/dashboard_service.py               总览经营摘要 / 任务排序
src/services/module_projection_service.py       导入数据到模块内容投影
src/api/routes/modules/dashboard.py             总览 API
src/services/action_plan_service.py             DecisionTaskDraft / ActionPlan 合约
src/services/module_task_service.py             旧 Demo 任务池；当前逐步退到兼容层
web_demo/index.html                             前端入口，已加载 report-task-sync.js?v=5.1.9
web_demo/modules/report/report-runtime.js       报表导入 / 回滚 / 删除记录
web_demo/modules/dashboard/page.js              产品化总览页
web_demo/decision-task.css                      行动顺序优先路径卡 / 待办路径摘要
web_demo/modules/task-report/decision-runtime.js 详情报告路径选择运行层
web_demo/modules/todo/page.js                   待办执行证据提交页
```

## 常用接口

```text
GET    /api/health
GET    /api/system/db-status
GET    /api/architecture/p0
GET    /api/architecture/context
GET    /api/architecture/tasks/persistence
GET    /api/architecture/tasks/repository
POST   /api/architecture/tasks/repository/create
POST   /api/architecture/tasks/repository/{task_id}/transition/{action}
POST   /api/architecture/tasks/repository/reset
POST   /api/architecture/tasks/sync-runtime
GET    /api/data/import-jobs
GET    /api/data/import-jobs/{import_job_id}
POST   /api/data/import-jobs/confirm
POST   /api/data/import-jobs/report
POST   /api/data/import-jobs/mock-alerts
POST   /api/data/report-tasks/sync-current
POST   /api/modules/agents/{module}/{entity_id}/tasks
POST   /api/modules/agents/creative/{product_id}/tasks
POST   /api/modules/todo/{task_id}/accept
POST   /api/modules/todo/{task_id}/submit
POST   /api/modules/todo/{task_id}/submit-evidence
POST   /api/modules/todo/{task_id}/review
POST   /api/modules/todo/{task_id}/review-evidence
POST   /api/modules/todo/{task_id}/complete
POST   /api/modules/todo/reset
POST   /api/system/reset-runtime-data?confirm=true
POST   /api/data/import/confirm
DELETE /api/data/versions/{data_version}?confirm=true
GET    /api/modules/dashboard
GET    /api/modules/product
GET    /api/modules/todo
GET    /api/modules/agents/{module}/{entity_id}
```

## P0 下一步实施顺序

```text
1. 数据库基础层：Async SQLAlchemy / Alembic / TenantScopedMixin / SoftDeleteMixin
2. UserContext：从 Demo Header 过渡到 JWT / Session
3. ScopedRepository：所有业务查询统一 tenant / store / deleted_at 过滤
4. Task 持久化镜像：task_status、task_events、task_logs、task_evidence + 状态机约束
5. TaskRepository Scoped Reads：通过 UserContext 读取可见任务并支持启动快照恢复
6. TaskRepository 写路径过渡：新增 create / transition / reset 的 repository API
7. 正式任务 API 切换：Agent 入池、待办接收/提交/复核/完成/重置已接入 repository 写路径
8. 报表任务同步桥：新增 report_task_repository_sync_service 与 /api/data/report-tasks/sync-current
9. 前端导入确认自动同步：report-task-sync.js 包装 confirmReportImport / importMockAlerts
10. 创意 Agent 入池同步：creative_task_repository_sync_service 接入 TaskRepository
11. 证据提交审计入库：task_evidence_audit_service 写入 task_evidence / task_logs
12. ImportJob 骨架：import_job_service /api/data/import-jobs/* import_jobs projection_jobs
13. Worker / Redis：导入、投影、预警、Agent 异步化与幂等重试
14. LLM Gateway：熔断、限流、配额、缓存、Schema 校验、Trace、降级模板
15. Audit / Logs：业务审计表 + JSON 技术日志 + trace_id
16. Nginx：前后端分离、HTTPS、限流、安全头
```
