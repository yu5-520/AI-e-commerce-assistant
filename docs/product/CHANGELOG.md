# Product Changelog

## v5.0.0 - 2026-06-21

### Product Decision
- V5 进入产品 Demo 操作系统阶段：保留原模块栏和模块功能，清除前端 MVP 托底业务内容。
- 首页不做导入入口，只作为产品化封面和经营摘要；没有导入数据时只显示暂无数据。
- 报表模块继续作为唯一数据入口；导入数据后，系统同时更新模块内容、生成预警、生成任务，并按账号权限切片。

### Changed
- `src/services/module_data_service.py` 清空运行态商品、竞品、上新、流量和报表详情托底数据，只保留空边界和报表模板。
- 新增 `src/services/module_projection_service.py`，把 DataVersion 快照投影成商品、流量和报表模块内容。
- `src/api/routes/modules/product.py` 改为从导入数据投影读取商品内容，并把任务绑定到商品模块和店铺权限。
- `src/api/routes/modules/traffic.py` 改为从订单导入数据投影读取流量承接内容，并把任务绑定到流量模块和店铺权限。
- `web_demo/modules/dashboard/page.js` 清除老板 / 总管 / 运营首页硬编码经营盘面，改成“暂无数据 / 经营摘要 / 模块入口”。
- `README.md` 和 `versioning/VERSION.md` 更新为 V5 主链路。

### Product Boundary
- 清托底数据，不清模块功能。
- 导入数据不只是生成任务，还要更新对应模块内容。
- 数据表、预警、任务都必须按店铺和账号权限切片。
- Agent 仍只做任务增强、执行说明、复核重点和回流草案，不越权执行真实经营动作。

## v4.5.3 - 2026-06-21

### Product Decision
- V4.5.3 把普通模块、任务生成、任务解析和回流任务都接入 LLM + RAG 增强。
- Product truth: ActionPlan 仍负责稳定判断和处理包合约；RAG 负责召回复核经验；LLM 负责把处理包写成更具体的执行说明、复核重点和风险提醒。

### Changed
- 新增 `src/services/agent_llm_enrichment_service.py`。
- `src/api/routes/modules/agents.py` 中的模块 Agent、任务生成 Agent、任务解析 Agent、周期 Agent 输出统一经过 LLM + RAG enrichment。
- `src/api/routes/modules/feedback_flywheel.py` 中的回流摘要、周期回流、经验卡草案输出统一经过 LLM enrichment。
- 输出新增 `retrievedCases`、`ragReferences`、`llmEnrichment`、`llmSummary`、`llmOperatorBrief`、`llmManagerReviewBrief`、`llmRiskCheck`、`llmFallbackUsed`。
- 详情页新增“方案补充”展示，展示执行说明、复核重点和风险提醒。

### Product Boundary
- LLM 不改变 `problemType`，不改写 ActionPlan 合约，不自动执行经营动作，不自动批准经验入库。LLM 失败时继续使用确定性 fallback。
