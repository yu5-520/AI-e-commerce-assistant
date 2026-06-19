# Changelog

## v4.4.0 - 2026-06-19

### Added
- Added `src/services/feedback_flywheel_service.py` for task-to-memory-to-RAG feedback analysis.
- Added `src/api/routes/modules/feedback_flywheel.py` with `/api/modules/feedback-flywheel`, `/api/modules/feedback-flywheel/cycle/{target}`, and `/api/modules/feedback-flywheel/cycle/{target}/draft`.
- Added automatic pending experience-card drafting after manager approval in the todo review flow.
- Added feedback metrics: task completion, pending tasks, memory approval, learning candidates, and problem distribution.
- Added frontend API client methods `feedbackFlywheel`, `feedbackCycle`, and `draftFeedbackCycle`.
- Added V4.4 health flags and smoke-test coverage for feedback flywheel endpoints and manager-review memory drafting.

### Changed
- FastAPI app version and frontend cache query strings are bumped to `4.4.0`.
- Approved tasks now carry a `feedbackDraft` payload so the operator / manager action can flow into RAG Memory review instead of staying only in logs.

### Product Engineering Rule
- 回流任务 Agent 可以生成经验卡草案和复盘摘要，但不能自动批准入库。正式 RAG 召回只使用复核通过的结构化经验。

## v4.3.0 - 2026-06-19

### Added
- Added `src/services/creative_vertical_agent_service.py` for vertical category title / main-image / selling-point planning.
- Added `POST /api/modules/agents/creative/{product_id}` and `GET /api/modules/agents/creative/{product_id}` for V4.3 creative strategy generation.
- Added `POST /api/modules/agents/creative/{product_id}/tasks` so a selected creative plan can become a human-reviewed test task in the unified task pool.
- Added platform expression rules for 淘宝、拼多多、抖音小店、通用.
- Added creative outputs: title variants, main-image directions, selling-point order, A/B test plan, creative task draft, RAG references, human decisions, and forbidden actions.
- Added frontend API client methods `creativeAgent` and `createCreativeTask`.
- Added V4.3 health flags and smoke-test coverage for the creative vertical Agent.

### Changed
- FastAPI app version and frontend cache query strings are bumped to `4.3.0`.
- Agent outputs now cover product expression strategy in addition to task generation, task playbooks, module analysis, and RAG memory.

### Product Engineering Rule
- 标题主图 Agent 不是“素材生成器”，而是类目表达策略生成器。它可以生成标题、主图方向、卖点排序和测试计划，但不能直接发布商品、改价、投放或回写店铺后台。

## v4.2.0 - 2026-06-19

### Added
- Added `src/services/task_agent_service.py` for RAG-driven task generation and task playbook Agents.
- Added `POST /api/modules/agents/tasks/generate` to convert module signals into task candidates using rules, structured RAG memory, confidence scoring, and human-confirmation gates.
- Added `GET /api/modules/agents/tasks/{task_id}/playbook` to explain active tasks with multiple operating styles: 稳健型、增长型、利润型.
- Added frontend API client methods `generateTaskCandidates` and `taskPlaybook`.
- Added V4.2 health flags and smoke-test coverage for generated task candidates, RAG references, task playbooks, and multi-style strategy output.

### Changed
- FastAPI app version and frontend cache query strings are bumped to `4.2.0`.
- Agent outputs now include task-generation confidence, RAG references, evidence requirements, and playbook strategies.
- Task generation can optionally create a task only when `autoCreate=true` and confidence clears the requested threshold.

### Product Engineering Rule
- 规则负责稳定触发，RAG 负责召回经验，Agent 负责生成任务草案和打法解释，人审负责是否进入任务池和是否执行。

## v4.1.0 - 2026-06-19

### Added
- Added `src/services/experience_memory_service.py` as the structured operation experience memory layer.
- Added `src/api/routes/modules/rag_memory.py` with `/api/modules/rag-memory`, `/api/modules/rag-memory/cases`, `/api/modules/rag-memory/search`, `/api/modules/rag-memory/feedback/tasks/{task_id}`, `/api/modules/rag-memory/cases/{case_id}/approve`, and `/api/modules/rag-memory/cases/{case_id}/reject`.
- Added seed playbooks and negative cases so V4 Agent workflows can retrieve approved operating experience before real RAG embeddings are connected.
- Added frontend API client methods for RAG memory summary, case listing, search, feedback drafting, approval, and rejection.
- Added V4.1 smoke-test coverage for memory search, task feedback-to-experience drafting, and owner / manager experience approval.

### Changed
- FastAPI app version and frontend cache query strings are bumped to `4.1.0`.
- `/api/modules` now includes the RAG memory routes while preserving `/api/accounts` role boundaries.
- Feedback from task handling can now become a pending experience card instead of being written directly into RAG.

### Product Engineering Rule
- RAG memory is not raw log storage. 日报、周报和任务日志必须先被提炼成经验卡，并经过质量分与人工复核，才能进入正式召回。

## v4.0.0 - 2026-06-19

### Added
- Added `src/services/module_agent_service.py` as the V4 advisory-only module Agent layer.
- Added `src/api/routes/modules/agents.py` with `/api/modules/agents`, `/api/modules/agents/{module}/{entity_id}`, `/api/modules/agents/{module}/{entity_id}/tasks`, and `/api/modules/agents/cycle/{target}`.
- Added V4 Agent panel to the independent detail report page so product / competitor / listing / traffic / report / task details can show Agent analysis and task drafts.
- Added V4 health flags and `docs/V4_MODULE_AGENT_RUNTIME.md`.

### Changed
- FastAPI app version and frontend cache query strings are bumped to `4.0.0`.
- Detail reports can now fetch module Agent advice without moving Agent into the highest control position.
- Agent-created task drafts still enter the existing unified task pool and keep the existing `/api/modules` task lifecycle and `/api/accounts` role boundary.

### Product Engineering Rule
- Agent belongs inside modules as an advisory layer. It can write suggestions, summaries, task drafts, and decision points, but it must not directly change price, ads, refunds, publishing state, marketplace data, or ERP / CRM records.

## v3.1.4 - 2026-06-17

### Added
- Added backend `/api/data/versions/{data_version}/detail` for one data-version detail payload.
- Added `web_demo/modules/report/report-runtime.js` as the normalized report runtime file.
- Added `web_demo/modules/manager/manager-modules.js` as the normalized manager module hub runtime file.

### Changed
- `data_version_service.py` now reports service version `3.1.4` instead of the stale rollback version.
- Data-version detail no longer depends on the browser stitching `/api/data/import-records` and `/api/data/alerts?limit=200`.
