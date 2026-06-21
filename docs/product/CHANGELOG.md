# Product Changelog

## v4.5.1 - 2026-06-21

### Product Decision
- V4.5.1 把 ActionPlan 从“字段展示”升级为“运营处理页”。
- Product truth: 后端给出的 `executionPackages`、`operatorAction`、`submitMetrics`、`acceptanceCriteria`、`failureThreshold` 应该被展示成处理包和任务卡，而不是塞进普通白卡里。

### Changed
- `web_demo/modules/task-report/page.js` 重做问题处理包渲染。
- 新增处理包卡片：处理目标、适用信息、运营动作、提交指标、复核标准、失败阈值、风险提醒。
- 新增任务草案卡片：任务标题、处理包、截止时间、来源、风险域、执行动作、提交材料、验收标准、失败阈值。
- 隐藏 `AP-refund-root-cause`、`AP-inventory-activity-control`、`ActionPlan` 等工程字段，避免给运营看。
- `web_demo/alert-report.css` 增加 iPad 友好的响应式 ActionPlan 布局，防止标题竖排、标签挤压和长文本横向溢出。

### Product Boundary
- UI 只做产品化展示，不改变 ActionPlan、LLM Gateway、权限、任务池、人审和复核链路。

## v4.5.0 - 2026-06-21

### Product Decision
- V4.5 不把系统直接 MCP 化，而是先做统一 LLM Gateway 和内部 Tool Gateway。
- Product truth: LLM 负责标题、主图文案、任务说明、经验卡草案等“表达增强”；problemType、ActionPlan、权限、任务池、人审和审计仍由确定性系统负责。
- MCP 只作为未来外部工具生态适配层，不能绕过内部任务池、账号权限、ActionPlan 和复核链路。

### Changed
- 新增统一模型层：`src/services/llm_provider_service.py`。
- 新增 LLM 防越权校验：`src/services/llm_guardrail_service.py`。
- 新增 LLM 调用追踪：`src/services/llm_trace_service.py`。
- 新增 Prompt 模板服务：`src/services/prompt_template_service.py`。
- 新增内部安全工具网关：`src/services/tool_gateway_service.py`。
- 新增 MCP 适配边界：`src/services/mcp_adapter_service.py`。
- 新增 `/api/llm/status`、`/api/llm/generate`、`/api/llm/traces`、`/api/llm/tools`、`/api/llm/mcp`。
- 新增 prompts 与 LLM 输出 schema。
- 创意 Agent 已接入第一层 LLM enrichment，输出 `llmEnrichment`、`llmTitleVariants`、`llmMainImageDirections`、`llmRiskCheck`、`llmPackagePreviews`。

### Product Boundary
- LLM 输出只作为草案，不能直接改价、投放、退款、发布商品、写 ERP / CRM 或自动批准经验入库。若 LLM 未启用、无 API Key、调用失败或命中越权动作，系统使用确定性 fallback。

## v4.4.2 - 2026-06-21

### Product Decision
- 将“模块发现任务”与“Agent 处理方案”彻底分层：模块只负责发现信号，`problemType` 决定处理包。
- Product truth: 商品、流量、竞品、上新、报表不应该各自套一套固定模板；同一个点击率问题无论来自商品页还是流量页，都应进入标题主图 / 详情页测试包。同一个退款问题无论来自商品页还是流量页，都应进入售后归因与承诺修正包。

### Changed
- 新增 `src/services/action_plan_service.py`，提供问题类型到处理包的确定性映射。
- `task_agent_service.py` 输出 `actionPlan`、`executionPackages`、`executionSteps`、`submitMetrics`、`acceptanceCriteria`、`failureThreshold`、`reviewFocus`。
- `module_agent_service.py` 的商品、流量、竞品、上新、报表、任务 Agent 全部改成先识别 problemType，再生成对应处理包。
- `web_demo/modules/task-report/page.js` 增加“问题处理包”展示，避免详情页继续显示通用的“先看报告 / 补证据 / 交复核”模板。
- `/api/health`、`/api/modules/agents` 和 `scripts/smoke_test_api.py` 已加入 V4.4.2 ActionPlan 验收。

### Product Boundary
- ActionPlan 只生成处理包和复核标准，不直接改价、投放、退款、发布商品或回写店铺后台。运营执行测试和处理，总管复核结果，回流 Agent 再沉淀经验卡。

## v4.4.1 - 2026-06-21

### Product Decision
- 将标题主图 Agent 从“给建议”进一步改成“生成可上架测试包”。
- Product truth: 运营不应该从零想标题和主图；Agent 负责根据垂直类目、平台风格、竞品信号和 RAG 经验生成多个测试包，运营负责选择、上架测试和提交结果。

### Changed
- `src/services/creative_vertical_agent_service.py` 新增 `testPackages` 输出。
- 每个测试包包含标题、主图方向、首图文案、卖点排序、适合流量、测试周期、提交指标、风险提醒和运营执行动作。
- `POST /api/modules/agents/creative/{product_id}/tasks` 支持 `packageIndex`，可以把指定测试包创建成任务。
- `web_demo/modules/task-report/page.js` 删除运营执行视角、AI 评估和 V4 模块 Agent 小字展示，改成“Agent 判断 → Agent 测试包 / 处理方案 → 任务草案 → 人工确认”。
- `scripts/smoke_test_api.py` 增加测试包和指定测试包建任务验收。

### Product Boundary
- Agent 生成测试包，运营上架测试。Agent 不直接发布商品、不改价、不投放、不回写店铺后台。

## v4.4.0 - 2026-06-19

### Product Decision
- V4.4 把“回流任务 Agent”从理念落到产品闭环：任务处理结果不再只进入日志，而是进入经验卡草案、日报 / 周报回流和 RAG 复核入库流程。
- Product truth: 回流不是把原始日志塞进 RAG，而是把运营动作、复核结论、结果指标和适用边界整理成结构化经验，再由老板 / 总管确认。
- 这让系统从“任务生成 / 任务解析 / 创意测试”继续升级为“任务处理 → 复盘回流 → 经验卡 → RAG 召回 → 反哺下一轮 Agent”。

### Changed
- 新增回流任务 Agent：`GET /api/modules/feedback-flywheel`。
- 新增日报 / 周报回流接口：`GET /api/modules/feedback-flywheel/cycle/{target}`。
- 新增周期经验卡草案接口：`POST /api/modules/feedback-flywheel/cycle/{target}/draft`。
- 新增 `src/services/feedback_flywheel_service.py`，负责学习候选、周期摘要、经验草案、反馈指标和 RAG 召回上下文。
- 总管复核通过任务后，待办接口会自动生成 `feedbackDraft` 经验卡草案，但仍需在 RAG Memory 中人工复核入库。
- 前端 API client 增加 `feedbackFlywheel`、`feedbackCycle`、`draftFeedbackCycle` 方法。
- V4.4 继续复用 RAG memory、统一任务池和 `/api/accounts` 权限边界。

### Product Boundary
- 当前 V4.4 不自动批准经验入库，不把日报 / 周报 / 日志原文直接写进正式 RAG，不自动执行经营动作。经验卡必须经过复核通过后，才可用于正式召回。

## v4.3.0 - 2026-06-19

### Product Decision
- V4.3 把“标题主图 Agent”从简单素材生成升级为“垂直类目表达策略 Agent”。
- Product truth: 真正有价值的不是生成几句标题，而是结合类目、平台、人群、竞品差评和历史测试，生成可被运营验证的表达方案。
- 这让系统从“任务生成 / 任务解析”继续升级为“类目表达策略 → 标题主图方案 → 小流量测试 → 任务回流”。

### Changed
- 新增标题主图垂直类目 Agent：`POST /api/modules/agents/creative/{product_id}`。
- 新增创意方案入任务池接口：`POST /api/modules/agents/creative/{product_id}/tasks`。
- 新增 `src/services/creative_vertical_agent_service.py`，负责商品事实、类目 Profile、平台表达规则、竞品信号、RAG 经验召回、标题方案、主图方向、卖点排序和 A/B 测试计划。
- 创意 Agent 输出：`titleVariants`、`mainImageDirections`、`sellingPointOrder`、`testPlan`、`taskDraft`、`ragReferences`、`humanDecision`、`forbiddenActions`。
- 内置平台表达规则：淘宝、拼多多、抖音小店、通用。
- 前端 API client 增加 `creativeAgent` 与 `createCreativeTask` 方法。
- V4.3 继续复用 RAG memory、统一任务池和 `/api/accounts` 权限边界。

### Product Boundary
- 当前 V4.3 只生成表达策略和测试计划，不生成真实图片文件，不自动发布商品，不改价、不投放、不回写 ERP / CRM / 店铺后台。创意方案若要进入执行，必须作为任务进入统一任务池并由人工确认。

## v4.2.0 - 2026-06-19

### Product Decision
- V4.2 把“任务生成”和“任务解析运营方式”正式拆成两个 Agent。
- Product truth: 任务不是 Agent 凭空生成，而是由规则命中、模块数据、RAG 经验召回和人工确认共同决定。
- 这让系统从“经验卡可召回”继续升级为“规则 + RAG 生成任务草案 → 多打法解析 → 人工选择执行”。

### Changed
- 新增自动解析生成任务 Agent：`POST /api/modules/agents/tasks/generate`。
- 新增任务解析运营方式 Agent：`GET /api/modules/agents/tasks/{task_id}/playbook`。
