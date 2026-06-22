# AI ERP 经营单元电商协同系统 MVP

> 当前版本：V5.1.3。新增 TaskRepository 写路径过渡层：保留现有 Demo UI 运行方式，同时开放基于 UserContext 的任务 create / transition / reset 数据库写入接口，任务状态流转会做状态机校验并同步持久化。

## 当前主链路

```text
报表模块导入数据表
↓
字段映射 / 数据校验 / 店铺归属 / 账号权限切片
↓
确认导入后自动入库
↓
DataVersion 数据版本进入后端追溯
↓
完整导入行持久化 imported_report_rows
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
src/core/context.py                         UserContext：tenant / user / role / store scope 统一注入
src/repositories/scoped_repository.py       ScopedRepository：tenant_id / deleted_at / Data Scope 查询约束
src/repositories/task_repository.py         TaskRepository：基于 UserContext 的任务持久化读写封装
src/services/task_repository_write_service.py TaskRepository 写路径过渡服务：create / transition / reset
src/services/p0_architecture_service.py     P0 SaaS 架构拆解运行态摘要
src/services/task_state_machine_service.py  P0 任务状态机与 SQLite 持久化镜像
src/api/routes/architecture.py              /api/architecture/p0 与 /api/architecture/context
src/api/routes/task_persistence.py          /api/architecture/tasks/persistence、repository、create、transition、reset 与 sync-runtime
docs/P0_SAAS_ARCHITECTURE.md                互联网大厂 SaaS P0 架构说明
requirements.txt                            补充 SQLAlchemy / asyncpg / Alembic / Redis / ARQ 等生产依赖
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

当前 P0 进度：**任务系统已经具备 SQLite mirror、TaskRepository scoped reads、启动快照恢复和写路径过渡 API。下一步是把正式模块任务接口、Agent 入池接口、待办动作按钮逐步切换到 repository 写路径。**

## 关键目录

```text
src/api/main.py                              FastAPI 入口，版本 5.1.3
src/core/context.py                          SaaS UserContext 依赖注入骨架
src/repositories/scoped_repository.py        多租户 / 软删除 / 数据范围统一查询约束
src/repositories/task_repository.py          任务 Repository：按 tenant / store / deleted_at 过滤读取与 upsert
src/services/task_repository_write_service.py 任务 Repository 写路径过渡服务
src/services/task_state_machine_service.py   任务状态机 / 持久化镜像 / task_events / task_logs / task_evidence
src/services/p0_architecture_service.py      P0 架构摘要服务
src/api/routes/architecture.py               P0 架构可视化 API
src/api/routes/task_persistence.py           任务持久化镜像状态、Repository 读写与同步 API
src/services/data_version_service.py          数据版本回滚 / Demo 删除
src/api/routes/data_import.py                 导入记录删除接口
src/services/dashboard_service.py             总览经营摘要 / 任务排序
src/services/module_projection_service.py      导入数据到模块内容投影
src/api/routes/modules/dashboard.py            总览 API
src/api/routes/modules/agents.py               Agent API，路径任务默认进入处理中
src/services/action_plan_service.py            DecisionTaskDraft / ActionPlan 合约
src/services/module_task_service.py            统一任务池；当前仍驱动 Demo，下一步逐步接入 repository 写路径
web_demo/index.html                            前端入口，缓存号 v5.0.9
web_demo/modules/report/report-runtime.js      报表导入 / 回滚 / 删除记录
web_demo/modules/dashboard/page.js             产品化总览页
web_demo/decision-task.css                     行动顺序优先路径卡 / 待办路径摘要
web_demo/modules/task-report/decision-runtime.js 详情报告路径选择运行层
web_demo/modules/todo/page.js                  待办执行证据提交页
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
POST   /api/system/reset-runtime-data?confirm=true
POST   /api/data/import/confirm
DELETE /api/data/versions/{data_version}?confirm=true
GET    /api/modules/dashboard
GET    /api/modules/product
GET    /api/modules/todo
GET    /api/modules/agents/{module}/{entity_id}
POST   /api/modules/agents/{module}/{entity_id}/tasks
```

## P0 下一步实施顺序

```text
1. 数据库基础层：Async SQLAlchemy / Alembic / TenantScopedMixin / SoftDeleteMixin
2. UserContext：从 Demo Header 过渡到 JWT / Session
3. ScopedRepository：所有业务查询统一 tenant / store / deleted_at 过滤
4. Task 持久化镜像：task_status、task_events、task_logs、task_evidence + 状态机约束
5. TaskRepository Scoped Reads：通过 UserContext 读取可见任务并支持启动快照恢复
6. TaskRepository 写路径过渡：新增 create / transition / reset 的 repository API
7. 正式任务 API 切换：把前端待办、Agent 入池、报表预警统一切到 repository 写路径
8. ImportJob：报表导入、DataVersion、ImportedRows、ProjectionJob、AlertEvent 串链
9. Worker / Redis：导入、投影、预警、Agent 异步化与幂等重试
10. LLM Gateway：熔断、限流、配额、缓存、Schema 校验、Trace、降级模板
11. Audit / Logs：业务审计表 + JSON 技术日志 + trace_id
12. Nginx：前后端分离、HTTPS、限流、安全头
```
