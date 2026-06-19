# AI ERP 经营单元电商协同系统 MVP

> V4.4：在 V4 模块 Agent、V4.1 RAG-ready 经验记忆层、V4.2 任务 Agent、V4.3 标题主图垂直类目 Agent 之上，新增“回流任务 Agent”。系统把任务处理、日报 / 周报、经验卡草案、复核入库和下一轮 RAG 召回连成闭环。

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
V4.2 任务生成 Agent：规则 + RAG + 置信度 + 任务草案
↓
V4.3 创意垂直 Agent：类目 Profile + 平台规则 + 竞品信号 + 标题主图测试
↓
模块 Agent 分析 / 摘要 / 任务草案 / 运营打法
↓
账号角色 / 权限 / 店群范围
↓
任务派发 / 运营提交 / 总管复核
↓
V4.4 回流任务 Agent：日报 / 周报 / 经验卡草案 / 反馈指标
↓
老板 / 总管确认入库
↓
RAG 经验召回
↓
/api/modules/* + /api/accounts + /api/data/*
↓
web_demo 模块化前端
```

核心原则：

```text
规则负责稳定触发，RAG 负责召回经验，Agent 负责生成任务草案、打法解释、类目表达策略和回流摘要，人审负责是否进入任务池、是否执行、是否批准经验入库。
```

Agent 与 RAG 边界：

```text
Agent 可以生成建议、草案、任务拆解、报表摘要、日报 / 周报初稿、任务候选、运营打法、标题主图方向、测试计划和经验卡草案。
RAG 可以召回类目知识、问题打法、历史案例、创意模式和失败边界。
Agent 不直接改价，不直接投放，不直接退款，不直接发布商品，不直接回写真实 ERP / CRM / 店铺数据。
RAG 不直接吃原始日志；日志必须先提炼为经验卡并复核。
```

## 2. 当前目录职责

```text
src/api/main.py                              FastAPI 唯一入口
src/api/routes/accounts.py                   V2 账号 / 角色 / 权限 API
src/api/routes/modules/__init__.py            当前模块 API 聚合入口
src/api/routes/modules/agents.py              V4 / V4.2 / V4.3 Agent API
src/api/routes/modules/rag_memory.py          V4.1 RAG 经验记忆 API
src/api/routes/modules/feedback_flywheel.py   V4.4 回流任务 Agent API
src/api/routes/modules/todo.py                待办 / 派发 / 提交 / 复核模块
src/api/routes/modules/task_report.py         详情报告模块
src/api/routes/health.py                      健康检查
src/services/module_agent_service.py          V4 模块 Agent 建议 / 草案 / 摘要服务
src/services/experience_memory_service.py     V4.1 结构化经验卡与轻量 RAG 检索
src/services/task_agent_service.py            V4.2 任务生成与任务打法 Agent
src/services/creative_vertical_agent_service.py V4.3 标题主图垂直类目 Agent
src/services/feedback_flywheel_service.py     V4.4 任务回流 / 经验飞轮 Agent
src/services/module_task_service.py           统一任务池与协同任务生命周期
src/services/module_data_service.py           后端模块 Mock 数据源
src/services/report_alert_service.py          V3 数据快照 / 预警事件 / 预警转任务
web_demo/index.html                           当前前端入口
web_demo/core/api-client.js                   前端 API 客户端
web_demo/modules/*/page.js                    模块化页面
scripts/smoke_test_api.py                     当前产品 API smoke test
versioning/CHANGELOG.md                       工程版本更新日志
versioning/VERSION.md                         当前版本与版本规则
docs/product/CHANGELOG.md                     产品更新日志
docs/V4.2_RAG_TASK_AGENTS.md                  V4.2 RAG 任务 Agent 说明
docs/V4.3_CREATIVE_VERTICAL_AGENT.md          V4.3 标题主图垂直类目 Agent 说明
docs/V4.4_FEEDBACK_FLYWHEEL.md                V4.4 回流飞轮说明
```

## 3. Agent 层级

```text
V4 模块 Agent：竞品、上新、售后、流量、报表、任务拆解、日报 / 周报。
V4.1 RAG Memory：结构化经验卡、复核入库、轻量召回。
V4.2 任务 Agent：自动解析生成任务、任务解析运营方式。
V4.3 创意 Agent：标题方案、主图方向、卖点排序、A/B 测试计划。
V4.4 回流 Agent：周期摘要、学习候选、经验卡草案、反馈指标。
```

## 4. V4.4 回流任务 Agent

```text
任务处理结果
↓
运营提交
↓
总管复核通过
↓
自动生成 feedbackDraft 经验卡草案
↓
日报 / 周报回流 Agent 汇总
↓
老板 / 总管确认入库
↓
RAG 召回给下一轮任务生成、任务解析、标题主图策略
```

V4.4 只生成经验草案，不自动批准入库。正式 RAG 召回仍只使用复核通过的结构化经验。

## 5. 当前产品 API

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

Agent 与回流接口：

```text
GET  /api/modules/agents
GET  /api/modules/agents/{module}/{entity_id}
POST /api/modules/agents/{module}/{entity_id}/tasks
GET  /api/modules/agents/cycle/{target}
POST /api/modules/agents/tasks/generate
GET  /api/modules/agents/tasks/{task_id}/playbook
POST /api/modules/agents/creative/{product_id}
GET  /api/modules/agents/creative/{product_id}
POST /api/modules/agents/creative/{product_id}/tasks
GET  /api/modules/feedback-flywheel
GET  /api/modules/feedback-flywheel/cycle/{target}
POST /api/modules/feedback-flywheel/cycle/{target}/draft
```

RAG Memory 接口：

```text
GET  /api/modules/rag-memory
GET  /api/modules/rag-memory/cases
GET  /api/modules/rag-memory/search
POST /api/modules/rag-memory/feedback/tasks/{task_id}
POST /api/modules/rag-memory/cases/{case_id}/approve
POST /api/modules/rag-memory/cases/{case_id}/reject
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

## 6. 账号角色

```text
老板账号：看全部店群、完整报告、任务流转、复核结果，可以下发任务和复核经验入库。
店群总管账号：接收老板任务，拆分给运营，复核运营提交结果，复核经验卡。
运营账号：只处理自己的任务，查看任务打法和创意测试方案，提交处理说明。
数据 / 财务账号：查看 ERP / CRM 报表和财务口径，不直接处理运营任务。
只读观察账号：只看总览、报告和日志，不创建、派发、提交或复核任务。
```

## 7. 本地运行

```bash
cp .env.example .env
bash scripts/start_server.sh
```

健康检查：

```bash
curl http://127.0.0.1:3000/api/health
curl http://127.0.0.1:3000/api/modules/dashboard
curl http://127.0.0.1:3000/api/modules/agents
curl http://127.0.0.1:3000/api/modules/feedback-flywheel
curl http://127.0.0.1:3000/api/modules/rag-memory
curl http://127.0.0.1:3000/api/accounts
```
