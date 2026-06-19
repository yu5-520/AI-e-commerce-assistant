# Product Changelog

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

## v3.1.3 - 2026-06-17

### Product Decision
- V3.1.3 cleans the report page hierarchy so operators see the report workflow first and data-version management last.
- Product truth: 导入记录是审计与回滚工具，不是报表页主流程。首页只展示摘要，详情页承载完整版本信息和回滚策略。
- Operator accounts can view version records and details, but rollback remains a management-level action.

### Changed
- Import records are moved to the bottom of the report page.
- Import records are compacted into list rows instead of large cards.
- Added a data-version detail route for full version information, alert impact, linked tasks, rollback records, and rollback controls.
- Rollback task strategy moved from the record list into the detail page.
- Rollback buttons are hidden from operator accounts and backend rollback is restricted to owner / manager / finance roles.
- Frontend assets now use `?v=3.1.3`; API and health versions are aligned.

### Product Boundary
- Current detail page uses existing snapshot, alert, and rollback data. Production should add immutable audit pages, permission logs, and owner approval for high-impact rollback.

## v3.1.2 - 2026-06-17

### Product Decision
- V3.1.2 completes the rollback product loop by defining what happens to tasks created by a wrong report version.
- Product truth: 预警可以回滚，但已经生成的待办不能假装不存在。它们必须被转人工复核、归档保留审计，或明确保持当前状态。
- This prevents silent task loss while keeping the system operable after wrong report uploads.

### Changed
- Data-version rollback now accepts a linked-task strategy.
- Default strategy is `review`: active linked tasks become `待复核` with `数据回滚待复核` workflow status.
- `archive` keeps audit history and removes linked active tasks from the active queue.
- `keep` records rollback impact but preserves current task status.
- Report page import records now include a linked-task strategy selector before rollback.
- Rollback result now reports affected alerts and affected tasks.
- Frontend dynamic assets now use `?v=3.1.2`; API and health versions are aligned.

### Product Boundary
- Current strategy is MVP-level task-state handling. Production should require manager / owner confirmation for high-impact rollback, task cancellation records, and immutable audit trails.

## v3.1.1 - 2026-06-17

### Product Decision
- V3.1.1 solves the operational problem of uploading the wrong report.
- Product truth: 上传报表是数据版本动作，不是不可逆动作。错误版本应该可以回滚，但必须留下审计记录。
- This makes the report runtime safer before connecting real ERP / CRM adapters.

### Changed
- Added import-record management under `/api/data/import-records`.
- Added data-version rollback under `/api/data/versions/{data_version}/rollback`.
- Report page now shows import records, active alerts, generated tasks, rollback state, and rollback history.
- Rolling back a version soft-removes that version's active alerts from dashboards and report warning lists.
- Linked tasks and historical evidence are kept for audit instead of being deleted.
- Added rollback UI styling and dynamic bootstrap loading.
- Frontend assets can be refreshed with `?v=3.1.1`; API and health versions are aligned.

### Product Boundary
- Current rollback is soft rollback for alert events. Production should also support task cancellation rules, attachment retention, owner approval for rollback, and irreversible audit logs.

## v3.1.0 - 2026-06-17

### Product Decision
- V3.1.0 makes inventory and customer-service handling independent operation centers.
- Product truth: 库存和售后不能长期藏在报表页里；报表负责触发预警，经营中心负责日常处理和任务归属。
- This gives the manager operation-module hub a complete six-module structure: 商品、竞品、上新、流量、库存、售后。

### Changed
- Added standalone inventory center API and page.
- Added standalone customer-service center API and page.
- Manager `经营模块` cards now open库存中心 and售后中心 instead of routing both into报表.
- Inventory center shows SKU count, danger / warning / normal inventory states, handling rules, and store-scoped task creation.
- Customer-service center shows abnormal / sensitive / normal service states, service归因 rules, and store-scoped task creation.
- Frontend assets now use `?v=3.1.0`; API and health versions are aligned.

### Product Boundary
- Current V3.1.0 data still derives from mock product and report-alert data. Production should connect inventory and service centers to ERP / CRM adapters, full row-level evidence, and persistent task records.
