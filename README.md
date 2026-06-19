# AI ERP 经营单元电商协同系统 MVP

> V4.3：在 V4 模块 Agent、V4.1 RAG-ready 经验记忆层、V4.2 任务 Agent 之上，新增“标题主图垂直类目 Agent”。系统把标题、主图、卖点排序和 A/B 测试计划，从简单素材生成升级为类目表达策略生成。

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
首页、商品、流量、报表、待办、日志、详情报告同步
↓
账号角色 / 权限 / 店群范围
↓
任务派发 / 运营提交 / 总管复核
↓
日报 / 周报 / 日志归档
↓
回流任务 Agent / 经验卡草案 / RAG 经验记忆
↓
/api/modules/* + /api/accounts + /api/data/*
↓
web_demo 模块化前端
```

核心原则：

```text
规则负责稳定触发，RAG 负责召回经验，Agent 负责生成任务草案、打法解释和类目表达策略，人审负责是否进入任务池和是否执行。
```

Agent 与 RAG 边界：

```text
Agent 可以生成建议、草案、任务拆解、报表摘要、日报 / 周报初稿、任务候选、运营打法、标题主图方向和测试计划。
RAG 可以召回类目知识、问题打法、历史案例、创意模式和失败边界。
Agent 不直接改价，不直接投放，不直接退款，不直接发布商品，不直接回写真实 ERP / CRM / 店铺数据。
RAG 不直接吃原始日志；日志必须先提炼为经验卡并复核。
```

## 2. 当前目录职责

```text
src/api/main.py                           FastAPI 唯一入口
src/api/routes/accounts.py                V2 账号 / 角色 / 权限 API
src/api/routes/modules/__init__.py         当前模块 API 聚合入口
src/api/routes/modules/agents.py           V4 / V4.2 / V4.3 Agent API
src/api/routes/modules/rag_memory.py       V4.1 RAG 经验记忆 API
src/api/routes/modules/todo.py             待办 / 派发 / 提交 / 复核模块
src/api/routes/modules/task_report.py      详情报告模块
src/api/routes/health.py                   健康检查
src/services/module_agent_service.py       V4 模块 Agent 建议 / 草案 / 摘要服务
src/services/experience_memory_service.py  V4.1 结构化经验卡与轻量 RAG 检索
src/services/task_agent_service.py         V4.2 任务生成与任务打法 Agent
src/services/creative_vertical_agent_service.py V4.3 标题主图垂直类目 Agent
src/services/module_task_service.py        统一任务池与协同任务生命周期
src/services/module_data_service.py        后端模块 Mock 数据源
src/services/report_alert_service.py       V3 数据快照 / 预警事件 / 预警转任务
web_demo/index.html                        当前前端入口
web_demo/core/api-client.js                前端 API 客户端
web_demo/modules/*/page.js                 模块化页面
scripts/smoke_test_api.py                  当前产品 API smoke test
versioning/CHANGELOG.md                    工程版本更新日志
versioning/VERSION.md                      当前版本与版本规则
docs/product/CHANGELOG.md                  产品更新日志
docs/V4.2_RAG_TASK_AGENTS.md               V4.2 RAG 任务 Agent 说明
docs/V4.3_CREATIVE_VERTICAL_AGENT.md       V4.3 标题主图垂直类目 Agent 说明
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

## 4. V4.1 经验记忆飞轮

V4.1 新增结构化经验卡：

```text
任务处理结果
↓
回流任务 Agent 提炼经验卡
↓
质量分 + 复核状态 + 适用 / 不适用条件
↓
老板 / 总管确认入库
↓
RAG 召回给下一轮任务生成和任务解析
```

经验卡分层：

```text
L0 原始日志 / 拒绝入库
L1 经验草案
L2 已复核经验
L3 高质量经验
L4 失败案例 / 避坑边界
```

## 5. V4.2 任务 Agent

V4.2 新增两个 Agent：

```text
自动解析生成任务 Agent
任务解析运营方式 Agent
```

任务生成链路：

```text
模块数据 / 指标异常
↓
规则命中
↓
问题类型判断
↓
RAG 经验召回
↓
置信度评分
↓
任务候选 / 证据要求 / 人工确认点
```

任务解析链路：

```text
待办任务
↓
问题类型
↓
RAG playbook / 历史案例 / 失败边界
↓
稳健型 / 增长型 / 利润型打法
↓
证据要求 / 验收标准 / 回流建议
```

## 6. V4.3 标题主图垂直类目 Agent

V4.3 新增创意垂直 Agent：

```text
商品事实
+ 类目 Profile
+ 平台表达规则
+ 竞品差评 / 机会点
+ RAG 历史经验
+ 当前任务目标
= 标题方案 / 主图方向 / 卖点排序 / A/B 测试计划
```

它不是直接生成最终图片，也不是自动发布商品，而是生成可进入任务池的表达策略与测试方案。

## 7. 当前产品 API

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

V4 / V4.2 / V4.3 Agent 接口：

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
```

V4.1 RAG Memory 接口：

```text
GET  /api/modules/rag-memory
GET  /api/modules/rag-memory/cases
GET  /api/modules/rag-memory/search
POST /api/modules/rag-memory/feedback/tasks/{task_id}
POST /api/modules/rag-memory/cases/{case_id}/approve
POST /api/modules/rag-memory/cases/{case_id}/reject
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

## 8. 账号角色

```text
老板账号：看全部店群、完整报告、任务流转、复核结果，可以下发任务和复核经验入库。
店群总管账号：接收老板任务，拆分给运营，复核运营提交结果，复核经验卡。
运营账号：只处理自己的任务，查看任务打法和创意测试方案，提交处理说明。
数据 / 财务账号：查看 ERP / CRM 报表和财务口径，不直接处理运营任务。
只读观察账号：只看总览、报告和日志，不创建、派发、提交或复核任务。
```

## 9. 本地运行

```bash
cp .env.example .env
bash scripts/start_server.sh
```

健康检查：

```bash
curl http://127.0.0.1:3000/api/health
curl http://127.0.0.1:3000/api/modules/dashboard
curl http://127.0.0.1:3000/api/modules/agents
curl http://127.0.0.1:3000/api/modules/rag-memory
curl http://127.0.0.1:3000/api/accounts
```
