# Changelog

## v4.5.1 - 2026-06-21

### Added
- Added dedicated ActionPlan package-card layout styles in `web_demo/alert-report.css`.
- Added productized task-draft card layout with meta fields, numbered operator steps, evidence, metrics, acceptance criteria, and failure thresholds.

### Changed
- `web_demo/modules/task-report/page.js` now renders problem handling packages and task drafts through dedicated components instead of generic report cards.
- Frontend asset cache query strings are bumped to `4.5.1`.
- FastAPI app and health version are bumped to `4.5.1`.

### Product Engineering Rule
- ActionPlan UI should show what operators need to execute and what managers need to review. Engineering IDs such as `AP-refund-root-cause`, `AP-inventory-activity-control`, and `ActionPlan` stay hidden from the product page.

## v4.5.0 - 2026-06-21

### Added
- Added `src/services/llm_provider_service.py` as the unified LLM Provider Gateway for OpenAI-compatible providers and deterministic fallback.
- Added `src/services/llm_guardrail_service.py`, `src/services/llm_trace_service.py`, and `src/services/prompt_template_service.py` for schema checks, forbidden-action checks, prompt loading, and local trace records.
- Added `src/services/tool_gateway_service.py` as the internal safe tool gateway and `src/services/mcp_adapter_service.py` as the future MCP boundary.
- Added `/api/llm/status`, `/api/llm/generate`, `/api/llm/traces`, `/api/llm/tools`, `/api/llm/tools/{tool_name}`, and `/api/llm/mcp`.
- Added prompt templates under `prompts/` and output schemas under `schemas/llm_outputs/`.
- Added `src/services/creative_llm_enrichment_service.py` and connected creative Agent responses to LLM enrichment with fallback.

### Changed
- FastAPI app version and frontend cache query strings are bumped to `4.5.0`.
- `src/api/routes/modules/agents.py` now registers LLM Gateway, Tool Gateway, and MCP Adapter boundary in the Agent registry.
- `.env.example` now includes V4.5 LLM Gateway settings: `LLM_ENABLED`, `LLM_MOCK_MODE`, `LLM_TRACE_ENABLED`, provider, model, base URL, key, timeout, temperature, and max tokens.
- `scripts/smoke_test_api.py` now validates LLM Gateway status, manual generation fallback, Tool Gateway safe / blocked tools, MCP boundary, and creative LLM enrichment.

### Product Engineering Rule
- LLM 只做表达增强和草案生成；ActionPlan、账号权限、任务池、人审、复核和审计链路保持确定性。MCP 只作为未来外部工具适配层，不替代内部 Tool Gateway。

## v4.4.2 - 2026-06-21

### Added
- Added `src/services/action_plan_service.py` as the deterministic problem-type → execution-package layer.
- Added ActionPlan outputs to task and module Agent payloads: `problemType`, `actionPlan`, `executionPackages`, `executionSteps`, `evidenceRequired`, `submitMetrics`, `acceptanceCriteria`, `failureThreshold`, and `reviewFocus`.
- Added frontend rendering for generic problem-type execution packages in `web_demo/modules/task-report/page.js`.
- Added V4.4.2 health flags and smoke-test coverage for problem-type ActionPlan outputs.

### Changed
- FastAPI app version and frontend cache query strings are bumped to `4.4.2`.
- `task_agent_service.py` no longer creates generic "补证据 / 交复核" task drafts; it routes module signals through ActionPlan packages.
- `module_agent_service.py` now uses ActionPlan for product, traffic, competitor, listing, report, and task detail Agent outputs.

### Product Engineering Rule
- 模块发现问题，problemType 决定处理包。Agent 不能按模块套同一模板；点击率、退款率、库存、竞品、报表等问题必须生成不同的执行包、提交指标和复核标准。

## v4.4.1 - 2026-06-21

### Added
- Added ready-to-test creative packages for the creative vertical Agent.
- Added selected package task creation through `packageIndex`.
- Added frontend task-report rendering for title / main-image test packages.

### Changed
- FastAPI app version and frontend cache query strings are bumped to `4.4.1`.
- Creative Agent output now includes package-level operator actions and submit metrics.

### Product Engineering Rule
- 标题主图 Agent 不是让运营继续想标题，而是生成可上架测试包。运营负责选择、测试和反馈。

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
