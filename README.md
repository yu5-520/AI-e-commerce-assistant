# AI ERP 经营单元电商协同系统 MVP

> 当前版本：V5.1.0。新增互联网大厂 SaaS P0 架构骨架：UserContext 依赖注入、ScopedRepository 强制数据范围约束、P0 架构可视化接口与生产依赖清单。当前更新以“不破坏 Demo 运行”为前提，先补工程底座，再进入任务落库与 ImportJob 事务链。

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

## V5.1.0 P0 SaaS 架构新增

```text
src/core/context.py                         UserContext：tenant / user / role / store scope 统一注入
src/repositories/scoped_repository.py       ScopedRepository：tenant_id / deleted_at / Data Scope 查询约束
src/services/p0_architecture_service.py     P0 SaaS 架构拆解运行态摘要
src/api/routes/architecture.py              /api/architecture/p0 与 /api/architecture/context
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

当前最重要的 P0 缺口：**任务、日志、任务事件仍需从内存数组迁移到数据库状态机。**

## 关键目录

```text
src/api/main.py                              FastAPI 入口，版本 5.1.0
src/core/context.py                          SaaS UserContext 依赖注入骨架
src/repositories/scoped_repository.py        多租户 / 软删除 / 数据范围统一查询约束
src/services/p0_architecture_service.py      P0 架构摘要服务
src/api/routes/architecture.py               P0 架构可视化 API
src/services/data_version_service.py          数据版本回滚 / Demo 删除
src/api/routes/data_import.py                 导入记录删除接口
src/services/dashboard_service.py             总览经营摘要 / 任务排序
src/services/module_projection_service.py      导入数据到模块内容投影
src/api/routes/modules/dashboard.py            总览 API
src/api/routes/modules/agents.py               Agent API，路径任务默认进入处理中
src/services/action_plan_service.py            DecisionTaskDraft / ActionPlan 合约
src/services/module_task_service.py            统一任务池；下一步 P0 需落库与状态机化
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
4. Task 持久化：tasks、task_events、task_logs、task_evidence + 严格状态机
5. ImportJob：报表导入、DataVersion、ImportedRows、ProjectionJob、AlertEvent 串链
6. Worker / Redis：导入、投影、预警、Agent 异步化与幂等重试
7. LLM Gateway：熔断、限流、配额、缓存、Schema 校验、Trace、降级模板
8. Audit / Logs：业务审计表 + JSON 技术日志 + trace_id
9. Nginx：前后端分离、HTTPS、限流、安全头
```
