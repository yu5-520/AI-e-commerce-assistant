# Product Changelog

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
- 新增 `src/services/task_agent_service.py`，负责规则命中、问题类型判断、RAG 召回、置信度评分、任务草案和多打法 playbook。
- 任务生成 Agent 输出：候选任务、问题类型、置信度、规则命中、证据要求、RAG 引用、人工确认点和禁止动作。
- 任务解析 Agent 输出：稳健型、增长型、利润型打法，适用条件、不适用条件、风险、证据要求和验收标准。
- 前端 API client 增加 `generateTaskCandidates` 与 `taskPlaybook` 方法。
- V4.2 继续复用统一任务池、RAG memory 和 `/api/accounts` 权限边界。

### Product Boundary
- 当前 V4.2 仍是规则 + 结构化 RAG 的 Agent-ready 层，不自动执行真实经营动作。`autoCreate=true` 也只是把高置信任务草案加入系统任务池，不会改价、投放、退款、发布或回写 ERP / CRM。

## v4.1.0 - 2026-06-19

### Product Decision
- V4.1 开始把“运营经验飞轮”落到代码层：任务处理结果不再只停留在日志，而是先提炼为结构化经验卡。
- Product truth: RAG 不是把日报、周报、任务日志原文塞进知识库，而是把复核过、有效果、有适用边界的处理方式沉淀成可召回经验。
- 这让系统从“Agent 生成建议”继续升级为“任务处理 → 经验卡 → 复核入库 → 下轮召回”。

### Changed
- 新增 RAG-ready 经验库底座：`src/services/experience_memory_service.py`。
- 新增 RAG Memory API：`/api/modules/rag-memory`、`/api/modules/rag-memory/cases`、`/api/modules/rag-memory/search`、`/api/modules/rag-memory/feedback/tasks/{task_id}`、`/api/modules/rag-memory/cases/{case_id}/approve`、`/api/modules/rag-memory/cases/{case_id}/reject`。
- 新增种子 playbook 与失败案例，先支持标签过滤 + 质量分 + 简单关键词召回。
- 新增任务反馈生成经验卡草案：运营提交、总管复核、前后指标变化会被整理为待复核经验卡。
- 经验卡入库新增质量门槛：总管 / 老板复核、质量分、指标变化、适用条件与不适用条件。
- 前端 API client 增加 RAG memory 调用方法，后续页面可以接入“回流候选 / 经验卡草案 / 复核入库”。
- V4.1 继续复用 `/api/modules` 模块入口和 `/api/accounts` 账号权限边界。

### Product Boundary
- 当前 V4.1 还是轻量 RAG-ready 层，不接真实向量库；先跑通结构化经验卡、人工复核和可控召回。后续再接 embedding、rerank、LLM 生成和 Agent 评估面板。

## v4.0.0 - 2026-06-19

### Product Decision
- V4 将 Agent 从“最高控制位”降到“模块增强层”。
- Product truth: Agent 适合做分析、摘要、任务草案和人工确认点，不适合直接接管价格、投放、退款、上新发布或真实店铺数据。
- 这让系统从“预警转任务”升级为“预警 → 模块 Agent 判断 → 人工确认 → 任务流转”。

### Changed
- 新增 V4 模块 Agent：竞品分析、上新标题 / 主图方案、售后归因、流量复盘、报表摘要、任务拆解、日报 / 周报。
- 详情报告页新增 V4 Agent 板块，展示 Agent 总结、证据、建议、任务草案、人工确认点和禁止动作。
- Agent 任务草案可以人工确认后加入统一任务池，继续走运营接收、提交、总管复核、日志归档链路。
- 新增 Agent API：`/api/modules/agents`、`/api/modules/agents/{module}/{entity_id}`、`/api/modules/agents/{module}/{entity_id}/tasks`、`/api/modules/agents/cycle/{target}`。
- V4 继续复用 `/api/modules` 模块入口和 `/api/accounts` 账号权限边界，Agent 不绕过角色、店铺和任务生命周期。
- 前端资产版本提升到 `?v=4.0.0`，API 与健康检查版本对齐。

### Product Boundary
- 当前 V4 是规则型 / Mock Agent-ready 层，用来先跑通产品结构。后续接 DeepSeek / OpenAI / RAG 时，只替换 Agent 推理内部，不改变任务池、人审边界和模块 API。

## v3.1.4 - 2026-06-17

### Product Decision
- V3.1.4 stops adding new features and repairs the current frontend / backend breakpoints.
- Product truth: once a feature starts depending on multiple frontend list calls, versioned file names, and duplicate loaders, the product becomes harder to operate and debug.
- Data-version detail should be a backend business payload. Frontend should display it, not reassemble it from unrelated lists.

### Changed
- Added backend data-version detail payload under `/api/data/versions/{data_version}/detail`.
- Report detail page now reads one detail payload containing the record, alerts, linked tasks, rollback, summary, and permissions.
- Data-version service version is aligned to `3.1.4`.
- Replaced `report-v311.js` with `report-runtime.js` and `manager-modules-v305.js` with `manager-modules.js`.
- Removed duplicate bootstrap dynamic loading; `index.html` is now the page module loading authority.
- Deleted unused old report and manager versioned runtime files.
- Frontend assets now use `?v=3.1.4`; API and health versions are aligned.

### Product Boundary
- Operation center and organization override files still carry old filename suffixes because they need a separate safe rename pass. They remain referenced and functional, but are now isolated as the remaining cleanup items.
