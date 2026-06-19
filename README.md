# AI ERP 经营单元电商协同系统 MVP

> V4：在原有 ERP / CRM 报表预警、账号权限、任务生命周期之上，新增“模块 Agent 增强层”。Agent 不放在最高控制位，而是放进商品、竞品、上新、流量、报表、待办和复盘链路中，生成分析、摘要、任务草案和人工确认点。

## 1. 当前主定位

本仓库当前只保留一条主产品链路：

```text
ERP / CRM Mock 数据 / 新导入报表
↓
数据校验与数据版本
↓
数据快照 / 指标快照
↓
异常规则判断
↓
预警事件 alert_event
↓
预警转任务 alert_to_task_bridge
↓
模块 Agent 分析 / 摘要 / 任务草案
↓
首页、商品、流量、报表、待办、日志、详情报告同步
↓
账号角色 / 权限 / 店群范围
↓
任务派发 / 运营提交 / 总管复核
↓
日报 / 周报 / 日志归档
↓
/api/modules/* + /api/accounts + /api/data/*
↓
web_demo 模块化前端
```

核心原则：

```text
ERP 决定经营单元，报表变化决定数据版本，异常规则生成预警，任务系统决定谁能看、谁能派、谁能处理、谁能复核，Agent 只增强模块判断，不直接执行经营动作。
```

Agent 边界：

```text
Agent 可以生成建议、草案、任务拆解、报表摘要、日报 / 周报初稿。
Agent 不直接改价，不直接投放，不直接退款，不直接发布商品，不直接回写真实 ERP / CRM / 店铺数据。
```

## 2. 当前目录职责

```text
src/api/main.py                         FastAPI 唯一入口
src/api/routes/accounts.py              V2 账号 / 角色 / 权限 API
src/api/routes/modules/__init__.py       当前模块 API 聚合入口
src/api/routes/modules/dashboard.py      总览模块
src/api/routes/modules/operating_unit.py 经营单元模块
src/api/routes/modules/product.py        商品模块
src/api/routes/modules/competitor.py     竞品模块
src/api/routes/modules/listing.py        上新模块
src/api/routes/modules/traffic.py        流量模块
src/api/routes/modules/report.py         报表模块
src/api/routes/modules/task_report.py    详情报告模块
src/api/routes/modules/agents.py         V4 模块 Agent API
src/api/routes/modules/todo.py           待办 / 派发 / 提交 / 复核模块
src/api/routes/modules/log.py            日志模块
src/api/routes/data_import.py            数据校验、导入记录、V3 报表触发预警
src/api/routes/health.py                 健康检查
src/api/routes/system.py                 系统状态与运行数据清理
src/services/account_service.py          V2 Mock 账号、角色、权限、店群范围
src/services/module_task_service.py      统一任务池与协同任务生命周期
src/services/task_report_service.py      详情报告与 Agent 评估边界
src/services/module_agent_service.py     V4 模块 Agent 建议 / 草案 / 摘要服务
src/services/module_data_service.py      后端模块 Mock 数据源
src/services/report_alert_service.py     V3 数据快照 / 预警事件 / 预警转任务
src/repositories/                       SQLite / JSONL 记录层
web_demo/index.html                      当前前端入口
web_demo/core/router.js                  前端路由生命周期
web_demo/core/api-client.js              前端 API 客户端
web_demo/stores/task-store.js            前端任务状态缓存
web_demo/modules/*/page.js               模块化页面
scripts/start_server.sh                  本机启动脚本
scripts/deploy_server.sh                 服务器部署脚本
scripts/check_version_governance.py      版本治理检查脚本
scripts/smoke_test_runtime.py            当前 workflow smoke test
scripts/smoke_test_api.py                当前产品 API smoke test
versioning/CHANGELOG.md                  工程版本更新日志
versioning/VERSION.md                    当前版本与版本规则
docs/product/CHANGELOG.md                产品更新日志
docs/product/mvp-scope.md                当前 MVP 范围与验收标准
docs/product/module-boundary.md          当前模块边界
docs/V3.0_REPORT_ALERT_RUNTIME.md        V3 报表触发预警说明
docs/V4_MODULE_AGENT_RUNTIME.md          V4 模块 Agent 说明
```

## 3. V4 模块 Agent

V4 当前内置 7 类 Agent：

```text
竞品数据收集分析 Agent
上新标题 / 主图方案多样生成 Agent
售后归因 Agent
流量复盘 Agent
报表摘要 Agent
任务拆解 Agent
日报 / 周报 Agent
```

它们输出统一结构：

```text
agentId
agentName
agentVersion
sourceModule
entityType
entityId
inputSnapshot
riskLevel
summary
evidence
suggestions
taskDrafts
humanDecision
forbiddenActions
nextStep
```

第一版是规则型 / Mock Agent-ready 层，用于跑通产品链路。后续接入 DeepSeek / OpenAI / RAG 时，只替换 Agent 服务内部的推理实现，不改变模块 API、任务池和人工确认边界。

## 4. 当前产品 API

前端主接口：

```text
GET  /api/modules/dashboard
GET  /api/modules/operating-unit
GET  /api/modules/product
GET  /api/modules/competitor
GET  /api/modules/listing
GET  /api/modules/traffic
GET  /api/modules/report
GET  /api/modules/todo
GET  /api/modules/log
GET  /api/modules/task-reports/tasks/{task_id}
GET  /api/modules/task-reports/candidates/{module}/{entity_id}
```

V4 Agent 接口：

```text
GET  /api/modules/agents
GET  /api/modules/agents/{module}/{entity_id}
POST /api/modules/agents/{module}/{entity_id}/tasks
GET  /api/modules/agents/cycle/{target}
```

V3 数据更新与预警接口：

```text
POST /api/data/import/report
POST /api/data/import/mock-alerts
GET  /api/data/versions
GET  /api/data/versions/latest
GET  /api/data/alerts
GET  /api/data/alerts/entity/{entity_type}/{entity_id}
GET  /api/data/v3-summary
```

账号与协同接口：

```text
GET  /api/accounts
GET  /api/accounts/me
GET  /api/accounts/users
GET  /api/accounts/roles
GET  /api/accounts/permissions
GET  /api/accounts/store-groups
GET  /api/accounts/stores
POST /api/modules/todo/{task_id}/assign
POST /api/modules/todo/{task_id}/submit
POST /api/modules/todo/{task_id}/review
POST /api/modules/todo/{task_id}/complete
POST /api/modules/todo/{task_id}/pin
POST /api/modules/todo/{task_id}/reorder
POST /api/modules/todo/reset
```

辅助接口：

```text
GET  /api/health
POST /api/data/validate
POST /api/data/import/mock
GET  /api/data/imports
GET  /api/approvals
GET  /api/approvals/records
POST /api/approvals/{task_id}/approve
POST /api/approvals/{task_id}/reject
GET  /api/system/db-status
POST /api/system/clear-runtime-data?confirm=true
```

## 5. 账号角色

```text
老板账号：看全部店群、完整报告、任务流转、复核结果，可以下发任务。
店群总管账号：接收老板任务，拆分给运营，复核运营提交结果。
运营账号：只处理自己的任务，提交处理说明。
数据 / 财务账号：查看 ERP / CRM 报表和财务口径，不直接处理运营任务。
只读观察账号：只看总览、报告和日志，不创建、派发、提交或复核任务。
```

## 6. 本地运行

```bash
cp .env.example .env
bash scripts/start_server.sh
```

本地访问：

```text
http://127.0.0.1:3000
```

健康检查：

```bash
curl http://127.0.0.1:3000/api/health
curl http://127.0.0.1:3000/api/modules/dashboard
curl http://127.0.0.1:3000/api/modules/agents
curl http://127.0.0.1:3000/api/accounts
```
