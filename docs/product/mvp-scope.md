# MVP 范围

## 1. 当前 MVP 定义

当前 v4.2.0 MVP 是一个 AI ERP 经营单元协同工作台，并新增模块 Agent 增强层、RAG-ready 运营经验记忆层、RAG 驱动的任务生成与任务解析 Agent。

```text
ERP / CRM Mock 数据
↓
数据校验与加载
↓
经营单元识别
↓
商品、竞品、上新、流量、报表模块
↓
候选预警与详情报告
↓
V4.2 任务生成 Agent：规则 + RAG + 置信度 + 任务候选
↓
V4 模块 Agent 分析 / 摘要 / 任务草案
↓
V4.2 任务解析 Agent：稳健型 / 增长型 / 利润型打法
↓
统一任务池
↓
账号角色 / 权限 / 店群范围
↓
任务派发 / 运营提交 / 总管复核
↓
日报 / 周报 / 日志记录与复盘
↓
V4.1 经验卡草案 / 复核入库 / RAG 召回
```

当前产品不是完整 ERP、完整 CRM、真实登录系统，也不是自动运营 Agent。V4 Agent 只是模块增强层，不是最高控制位；V4.1 RAG 经验记忆只召回复核过的结构化经验；V4.2 任务 Agent 只生成任务候选和打法解释，不直接执行经营动作。

## 2. 当前必须保留

```text
src.api.main:app
/api/modules/*
/api/accounts
web_demo/index.html
web_demo/core/router.js
web_demo/core/api-client.js
web_demo/stores/task-store.js
web_demo/modules/*/page.js
scripts/check_version_governance.py
scripts/smoke_test_runtime.py
scripts/smoke_test_api.py
versioning/CHANGELOG.md
versioning/VERSION.md
docs/product/CHANGELOG.md
```

## 3. 当前产品接口

模块接口：

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

V4 / V4.2 Agent 接口：

```text
GET  /api/modules/agents
GET  /api/modules/agents/{module}/{entity_id}
POST /api/modules/agents/{module}/{entity_id}/tasks
GET  /api/modules/agents/cycle/{target}
POST /api/modules/agents/tasks/generate
GET  /api/modules/agents/tasks/{task_id}/playbook
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

账号与任务协同接口：

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

## 4. 当前验收标准

本地脚本必须通过：

```bash
python scripts/check_version_governance.py
python scripts/smoke_test_runtime.py
python scripts/smoke_test_api.py
```

服务必须可以启动：

```bash
uvicorn src.api.main:app --host 127.0.0.1 --port 3000
```

关键接口必须可访问：

```bash
curl http://127.0.0.1:3000/api/health
curl http://127.0.0.1:3000/api/modules/dashboard
curl http://127.0.0.1:3000/api/modules/agents
curl http://127.0.0.1:3000/api/modules/rag-memory
curl http://127.0.0.1:3000/api/accounts
```

前端必须通过：

```text
web_demo/index.html
↓
web_demo/core/router.js
↓
web_demo/modules/*/page.js
↓
/api/modules/* + /api/accounts
```

## 5. 当前不做

```text
不接真实 ERP API
不接真实 CRM API
不登录真实店铺后台
不接真实企业 SSO
不执行真实 RPA
不自动改价
不自动上架 / 下架
不自动报名活动
不自动投放广告
不自动群发客户
不自动处理退款
不自动回写真实 ERP / CRM
不把未复核原始日志直接写入 RAG
不保存真实客户隐私
```

## 6. 账号系统边界

```text
老板账号：全局观察、下发任务、查看复核结果，复核经验入库。
店群总管账号：拆分任务、派发运营、复核提交，复核经验卡。
运营账号：只处理自己的任务并提交，可查看任务打法。
数据 / 财务账号：看报表和财务数据，不直接处理运营任务。
只读观察账号：只读看板、报告、日志。
```

## 7. Agent / RAG 边界

```text
Agent 可以生成建议、草案、任务拆解、报表摘要、日报 / 周报初稿、任务候选和任务打法。
RAG 可以召回复核过的类目知识、问题打法、历史案例和失败边界。
Agent 不直接改价，不直接投放，不直接退款，不直接发布商品，不直接回写真实 ERP / CRM / 店铺数据。
RAG 不直接吃原始日志；日志必须先提炼为经验卡并复核。
```

## 8. 当前结论

当前阶段只追求：

> 用 Mock ERP / CRM 数据跑通经营单元识别、候选预警、模块 Agent 建议、任务生成、任务打法、详情报告、统一任务池、账号协同、派发提交复核、日志归档、经验卡草案和 RAG 召回闭环。

任何新增页面、接口、Agent、脚本或文档，都必须先确认不会偏离当前可运行主线。
