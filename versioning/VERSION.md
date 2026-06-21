# Version

Current Version: v5.0.3

## Version History

- v5.0.3: Added V5 runtime cleanup to solve stale SQLite residual data after removing frontend fallback content. The API applies a one-time startup cleanup marker, exposes `/api/system/reset-runtime-data`, clears module projections / report rows / alerts / tasks, and bumps frontend cache to V5.0.3.
- v5.0.2: Fixed the remaining V5 projection breakpoints by binding Module Agent, Task Agent, and Creative Agent to ModuleProjection data instead of old fallback arrays. Removed duplicate legacy report backend route and duplicate legacy report frontend page. Bumped API runtime and frontend cache to V5.0.2.
- v5.0.1: Closed the V5 flow-link breakpoints by removing runtime seed tasks, persisting full normalized import rows for module projection, routing the report module through the V5 projection route, and keeping report task creation available after the route switch.
- v5.0.0: Cleared MVP-stage runtime business fallback content while keeping the original module navigation and module functions. Added `module_projection_service.py` so report imports can project data into product / traffic / report views, and updated product / traffic routes plus the dashboard page to show empty state until imported data creates module content, alerts, and scoped tasks.
- v4.5.3: Added Module / Task / Feedback LLM + RAG enrichment through `src/services/agent_llm_enrichment_service.py`. Module Agent, task generation, task playbook, and feedback flywheel outputs now include `retrievedCases`, `ragReferences`, `llmEnrichment`, `llmSummary`, `llmOperatorBrief`, `llmManagerReviewBrief`, `llmRiskCheck`, and fallback metadata while problemType and ActionPlan remain deterministic.
- v4.5.2: Removed task-report top notice bars for Agent refresh and task creation, changed task creation to local button loading / inline error feedback, and made “重新生成 Agent 方案” preserve the current report and old Agent output if refresh fails.
- v4.5.1: Productized the ActionPlan detail UI. `web_demo/modules/task-report/page.js` now renders problem handling packages and task drafts as dedicated product cards with numbered operator steps, submit metrics, review criteria, failure thresholds, and hidden engineering IDs; `web_demo/alert-report.css` adds responsive iPad-safe layout styles.
- v4.5.0: Added the unified LLM Gateway with `src/services/llm_provider_service.py`, `llm_guardrail_service.py`, `llm_trace_service.py`, `prompt_template_service.py`, `tool_gateway_service.py`, `mcp_adapter_service.py`, `/api/llm/*` routes, prompt templates, LLM output schemas, `.env.example` settings, and first creative-Agent LLM enrichment. MCP is kept as a future external tool adapter behind Tool Gateway, not the primary model interface.
