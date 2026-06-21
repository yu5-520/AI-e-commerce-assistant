# AI ERP 经营单元电商协同系统 MVP

> 当前版本：V5.0.4。V5 保留原有模块栏和模块功能，清除前端 MVP 托底业务内容；报表模块负责导入数据表，导入后按账号权限生成模块内容、预警和任务。V5.0.4 已清理老板端、总管端、经营单元和总览页的演示盘面，所有角色视图都以导入数据和任务池为准。

## 当前主链路

```text
V5 启动时一次性清理旧 SQLite 残留
↓
首页 / 模块进入真实空状态
↓
报表模块导入数据表
↓
字段映射 / 数据校验 / 店铺归属 / 账号权限切片
↓
DataVersion 数据版本
↓
完整导入行持久化 imported_report_rows
↓
ModuleProjection：更新商品、竞品、上新、流量、报表、首页摘要、经营单元摘要
↓
AlertEvent：系统规则生成预警事件
↓
模块 Agent：基于 ModuleProjection 数据增强任务候选
↓
ActionPlan：problemType → 针对性处理包
↓
RAG Memory：召回复核过的结构化经验
↓
LLM 增强：执行说明、复核重点、风险提醒、经验卡表达
↓
统一任务池：按模块归属和账号权限派发 / 接收 / 提交 / 复核 / 归档
↓
回流 Agent：日报 / 周报 / 学习候选 / 经验卡草案
↓
RAG Memory：老板 / 总管复核入库 → 下一轮召回
```

核心规则：**首页是产品化封面和经营摘要，不做导入入口；报表模块是唯一数据导入入口；清除托底数据但不清模块功能；导入数据后同时刷新模块内容和任务；经营单元、老板端、总管端、运营端都遵循同一个空状态标准；数据、预警、任务和 Agent 输入都按账号权限切片。**

## 关键目录

```text
src/api/main.py                              FastAPI 入口，版本 5.0.4
src/api/routes/system.py                      系统状态与运行态清空接口
src/services/system_service.py                V5 runtime reset / one-time cleanup
src/api/routes/modules/operating_unit.py      V5 经营单元投影接口
src/api/routes/modules/__init__.py            模块 API 聚合
src/api/routes/modules/agents.py              Agent 注册表与 Agent API
src/api/routes/llm.py                         LLM Gateway API
src/api/routes/modules/feedback_flywheel.py   回流任务 Agent API
src/api/routes/modules/rag_memory.py          RAG Memory API
src/api/routes/modules/todo.py                统一任务池生命周期
src/api/routes/modules/product.py             V5 商品模块数据投影
src/api/routes/modules/traffic.py             V5 流量模块数据投影
src/api/routes/modules/report_v5.py           V5 报表模块投影路由
src/services/import_row_store_service.py      V5 完整导入行持久化
src/services/module_projection_service.py     V5 导入数据 → 模块内容投影
src/services/module_task_service.py           V5 空任务池运行态 / 数据生成任务
src/services/module_agent_service.py          V5 ModuleProjection Agent
src/services/task_agent_service.py            V5 TaskProjection Agent
src/services/creative_vertical_agent_service.py V5 projected product creative Agent
src/services/module_data_service.py           V5 空运行态边界，不再放前端托底业务内容
src/services/action_plan_service.py           问题类型处理包
src/services/agent_llm_enrichment_service.py  模块 / 任务 / 回流 LLM + RAG 增强
web_demo/index.html                           前端入口，缓存号 v5.0.4
web_demo/core/api-client.js                   前端 API 客户端，reset 同步清理管理视角 localStorage
web_demo/modules/dashboard/page.js            V5 总览空状态 / 经营摘要
web_demo/modules/operating-unit/page.js       V5 经营单元空状态 / 经营摘要
web_demo/modules/manager/page.js              V5 总管端空状态 / 任务池视图
web_demo/modules/executive/page.js            V5 老板端空状态 / 投影视图
scripts/smoke_test_api.py                     当前 API 主验收
```

## 常用接口

```text
GET  /api/health
GET  /api/system/db-status
POST /api/system/reset-runtime-data?confirm=true
POST /api/system/reset-legacy-runtime-once
GET  /api/data/templates
POST /api/data/preview
POST /api/data/import/confirm
GET  /api/data/versions
GET  /api/data/alerts
GET  /api/modules/operating-unit
GET  /api/modules/product
GET  /api/modules/traffic
GET  /api/modules/report
GET  /api/modules/todo
GET  /api/accounts
```

## 本地运行

```bash
cp .env.example .env
bash scripts/start_server.sh
```

健康检查：

```bash
curl http://127.0.0.1:3000/api/health
curl http://127.0.0.1:3000/api/system/db-status
curl -X POST 'http://127.0.0.1:3000/api/system/reset-runtime-data?confirm=true'
curl http://127.0.0.1:3000/api/modules/operating-unit
curl http://127.0.0.1:3000/api/modules/product
curl http://127.0.0.1:3000/api/modules/todo
```

## 当前不做

```text
不接真实 ERP / CRM
不登录真实店铺后台
不自动改价 / 投放 / 退款 / 发布商品
不自动批准经验卡入库
不把原始日志直接写入正式 RAG
不让 MCP 绕过内部权限和任务池
不保存真实客户隐私
```
