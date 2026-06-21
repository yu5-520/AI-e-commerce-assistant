# AI ERP 经营单元电商协同系统 MVP

> 当前版本：V4.5.1。README 只保留当前主线、入口和运行方式；详细边界以 `docs/product/module-boundary.md` 为准，MVP 范围以 `docs/product/mvp-scope.md` 为准，版本记录以 `versioning/CHANGELOG.md` 和 `docs/product/CHANGELOG.md` 为准。

## 当前主链路

```text
ERP / CRM Mock 数据 / 导入报表
↓
数据校验 / 数据版本 / 预警事件
↓
模块 Agent：商品、竞品、上新、流量、报表、任务拆解
↓
V4.2 任务 Agent：规则 + RAG + 置信度 → 任务候选 / 运营打法
↓
V4.4.2 ActionPlan：problemType → 针对性处理包
↓
V4.5 LLM Gateway：标题、主图文案、任务说明、经验卡草案的表达增强
↓
V4.3 创意 Agent：类目 Profile + 平台规则 + 竞品信号 → 标题主图测试包
↓
统一任务池：派发 / 接收 / 提交 / 复核 / 归档
↓
V4.4 回流 Agent：日报 / 周报 / 学习候选 / 经验卡草案
↓
RAG Memory：老板 / 总管复核入库 → 下一轮召回
```

核心规则：**ActionPlan 决定处理包，LLM 只做表达增强；Agent 可以建议和生成草案，但不能越权执行；RAG 只召回复核过的结构化经验，不直接吃原始日志。**

## 关键目录

```text
src/api/main.py                              FastAPI 入口
src/api/routes/modules/__init__.py            模块 API 聚合
src/api/routes/modules/agents.py              Agent 注册表与 Agent API
src/api/routes/llm.py                         V4.5 LLM Gateway API
src/api/routes/modules/feedback_flywheel.py   V4.4 回流任务 Agent API
src/api/routes/modules/rag_memory.py          RAG Memory API
src/api/routes/modules/todo.py                统一任务池生命周期
src/services/module_agent_service.py          V4 模块 Agent
src/services/task_agent_service.py            V4.2 任务 Agent
src/services/action_plan_service.py           V4.4.2 问题类型处理包
src/services/llm_provider_service.py          V4.5 统一 LLM Provider Gateway
src/services/tool_gateway_service.py          V4.5 内部安全 Tool Gateway
src/services/mcp_adapter_service.py           V4.5 MCP 外部适配边界
src/services/creative_vertical_agent_service.py V4.3 创意 Agent
src/services/creative_llm_enrichment_service.py V4.5 创意 LLM 增强
src/services/feedback_flywheel_service.py     V4.4 回流 Agent
src/services/experience_memory_service.py     结构化经验卡 / 轻量 RAG
web_demo/index.html                           前端入口
web_demo/modules/feedback/page.js             经验回流页面
scripts/smoke_test_api.py                     当前 API 主验收
```

## 常用接口

```text
GET  /api/health
GET  /api/llm/status
POST /api/llm/generate
GET  /api/llm/traces
GET  /api/llm/tools
GET  /api/llm/mcp
GET  /api/modules/agents
GET  /api/modules/feedback-flywheel
GET  /api/modules/rag-memory
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
curl http://127.0.0.1:3000/api/llm/status
curl http://127.0.0.1:3000/api/modules/agents
curl http://127.0.0.1:3000/api/modules/feedback-flywheel
curl http://127.0.0.1:3000/api/modules/rag-memory
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
