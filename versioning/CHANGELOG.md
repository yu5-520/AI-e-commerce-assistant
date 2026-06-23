# Changelog

## v9.0.0 - 2026-06-24

### Added
- Added V9 SaaS enterprise consistency baseline as the active product trunk.
- Added `docs/V9_SAAS_CONSISTENCY_BASE.md` to define repository, frontend, backend, three-tier isolation, RAG isolation, permissions, audit, deployment, and smoke-test governance.
- Kept `/api/modules` and `/api/accounts` as stable product entrypoints for frontend modules and account scope.

### Changed
- FastAPI runtime is bumped to `9.0.0` through the `API_VERSION` constant.
- README is rewritten from the V5 PostgreSQL mirror entrypoint into the V9 SaaS enterprise baseline entrypoint.
- `scripts/check_version_governance.py` now reads `API_VERSION = "X.Y.Z"` as the primary runtime version source and still supports literal FastAPI `version="X.Y.Z"` fallback.

### Product Engineering Rule
- V9 does not add new frontend business modules and does not extend V8 algorithms. V9 consolidates V1-V8 capabilities into a SaaS enterprise foundation: repository consistency, frontend consistency, backend consistency, pricing-tier isolation, RAG isolation, permission/audit governance, deployment-mode governance, and test acceptance consistency.

## v4.5.3 - 2026-06-21

### Added
- Added `src/services/agent_llm_enrichment_service.py` for Module / Task / Feedback LLM + RAG enrichment.
- Module Agent outputs now include `retrievedCases`, `ragReferences`, `llmEnrichment`, `llmSummary`, `llmOperatorBrief`, `llmManagerReviewBrief`, `llmRiskCheck`, and `llmFallbackUsed`.
- Task generation and task playbook endpoints now wrap ActionPlan payloads with RAG cases and LLM enrichment.
- Feedback flywheel summary, cycle summary, and experience-card drafts now use LLM enrichment while keeping human review gates.
- Task-report frontend now renders a `方案补充` section when enriched briefs are available.

### Changed
- FastAPI app, health flags, Agent registry, frontend asset cache query strings, and version docs are bumped to `4.5.3`.
- `src/api/routes/modules/agents.py` routes module, task-generation, task-playbook, and cycle Agent outputs through the enrichment service.
- `src/api/routes/modules/feedback_flywheel.py` routes feedback outputs through the enrichment service.

### Product Engineering Rule
- RAG supplies reviewed experience cases; LLM refines wording and execution briefs. `problemType`, `ActionPlan`, permissions, task lifecycle, and human review remain deterministic.

## v4.5.2 - 2026-06-21

### Changed
- Removed top notice bars such as “Agent 任务草案提交中...” from the task-report page.
- Task creation and creative-package creation now use only local button loading state and inline error feedback.
- “重新生成 Agent 方案” no longer schedules a full route refresh; it keeps the current report visible, replaces only the Agent result when successful, and preserves the old Agent result when generation fails.
- Frontend asset cache query strings are bumped to `4.5.2`.
- FastAPI app and health version are bumped to `4.5.2`.

### Product Engineering Rule
- Task-report actions should not expose internal process copy. Users see the action result through button state, task navigation, or local failure feedback.

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
- FastAPI app version and frontend asset cache query strings are bumped to `4.5.0`.
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
