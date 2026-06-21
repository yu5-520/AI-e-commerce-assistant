# AI ERP 经营单元电商协同系统 MVP

> 当前版本：V5.0.3。V5 保留原有模块栏和模块功能，清除前端 MVP 托底业务内容；报表模块负责导入数据表，导入后按账号权限生成模块内容、预警和任务。V5.0.3 已加入运行态清空能力：旧服务器 SQLite 残留会在首次启动时自动清空一次，之后新导入数据不会被反复清空。

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
ModuleProjection：更新商品、竞品、上新、流量、报表、首页摘要
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

核心规则：**首页是产品化封面和经营摘要，不做导入入口；报表模块是唯一数据导入入口；清除托底数据但不清模块功能；导入数据后同时刷新模块内容和任务；数据、预警、任务和 Agent 输入都按账号权限切片；ActionPlan 决定处理包，RAG 召回复核经验，LLM 只做表达增强。**

## 关键目录

```text
src/api/main.py                              FastAPI 入口，V5.0.3 启动清理旧运行态
src/api/routes/system.py                      系统状态与运行态清空接口
src/services/system_service.py                V5 runtime reset / one-time cleanup
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
src/services/llm_provider_service.py          统一 LLM Provider Gateway
src/services/tool_gateway_service.py          内部安全 Tool Gateway
src/services/mcp_adapter_service.py           MCP 外部适配边界
src/services/feedback_flywheel_service.py     回流 Agent
src/services/experience_memory_service.py     结构化经验卡 / 轻量 RAG
web_demo/index.html                           前端入口，缓存号 v5.0.3
web_demo/core/api-client.js                   前端 API 客户端，含 resetRuntimeData
web_demo/modules/report/report-runtime.js     唯一报表前端运行文件
web_demo/modules/dashboard/page.js            V5 首页空状态 / 经营摘要
scripts/smoke_test_api.py                     当前 API 主验收
```

## 常用接口

```text
GET  /api/health
GET  /api/system/db-status
POST /api/system/reset-runtime-data?confirm=true
POST /api/system/reset-legacy-runtime-once
GET  /api/llm/status
POST /api/llm/generate
GET  /api/llm/traces
GET  /api/llm/tools
GET  /api/llm/mcp
GET  /api/data/templates
POST /api/data/preview
POST /api/data/import/confirm
GET  /api/data/versions
GET  /api/data/alerts
GET  /api/modules/product
GET  /api/modules/traffic
GET  /api/modules/report
GET  /api/modules/todo
GET  /api/accounts
```

完整 API 边界见 `docs/product/module-boundary.md`。

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
curl http://127.0.0.1:3000/api/modules/product
curl http://127.0.0.1:3000/api/modules/traffic
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
