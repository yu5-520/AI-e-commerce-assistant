# Version

Current Version: v4.5.0

## Version History

- v4.5.0: Added the unified LLM Gateway with `src/services/llm_provider_service.py`, `llm_guardrail_service.py`, `llm_trace_service.py`, `prompt_template_service.py`, `tool_gateway_service.py`, `mcp_adapter_service.py`, `/api/llm/*` routes, prompt templates, LLM output schemas, `.env.example` settings, and first creative-Agent LLM enrichment. MCP is kept as a future external tool adapter behind Tool Gateway, not the primary model interface.
- v4.4.2: Added the problem-type Action Plan layer with `src/services/action_plan_service.py`; task and module Agents now output `problemType`, `actionPlan`, `executionPackages`, `executionSteps`, `evidenceRequired`, `submitMetrics`, `acceptanceCriteria`, `failureThreshold`, and `reviewFocus` so each module signal becomes a targeted handling package instead of one generic task-breakdown template.
- v4.4.1: Refined the creative vertical Agent into a ready-to-test package generator. Added `testPackages`, selected-package task creation with `packageIndex`, operator execution steps, submit metrics, task-report page cleanup, and smoke-test coverage for title / main-image test packages.
- v4.4.0: Added the feedback flywheel Agent with `src/services/feedback_flywheel_service.py`, `/api/modules/feedback-flywheel`, `/api/modules/feedback-flywheel/cycle/{target}`, `/api/modules/feedback-flywheel/cycle/{target}/draft`, automatic experience-card drafting on manager approval, feedback metrics, frontend client methods, V4.4 health flags, and smoke-test coverage.
- v4.3.0: Added the vertical category creative Agent with `src/services/creative_vertical_agent_service.py`, `/api/modules/agents/creative/{product_id}`, `/api/modules/agents/creative/{product_id}/tasks`, category profiles, platform expression rules, competitor-signal transformation, title variants, main-image directions, selling-point ordering, A/B test plans, frontend client methods, V4.3 health flags, and smoke-test coverage.
- v4.2.0: Added RAG-driven task generation and task playbook Agents with `src/services/task_agent_service.py`, `/api/modules/agents/tasks/generate`, `/api/modules/agents/tasks/{task_id}/playbook`, multi-style operating playbooks, confidence scoring, RAG references, frontend client methods, V4.2 health flags, and smoke-test coverage.
- v4.1.0: Added the RAG-ready operation experience memory layer with structured experience cards, seed playbooks, negative cases, `/api/modules/rag-memory` endpoints, feedback-to-experience drafting, owner/manager approval and rejection, frontend API client methods, V4.1 health flags, and smoke-test coverage for memory search and feedback learning.
- v4.0.0: Added the V4 module Agent layer with advisory-only Agent service, `/api/modules/agents` endpoints, Agent task-draft creation, detail-report Agent panel, cycle report Agent, V4 health flags, frontend asset cache bump, and documentation. Agent outputs suggestions, summaries, task drafts, and human decision points, but does not directly execute price, ads, refund, publish, or ERP / CRM write actions.
- v3.1.4: Fixed frontend / backend breakpoints by adding backend data-version detail payloads, aligning data-version service version to 3.1.4, replacing versioned report and manager module filenames with normalized runtime files, removing duplicate bootstrap dynamic loading, and deleting unused report / manager versioned runtime files.
- v3.1.3: Reworked the report page hierarchy by moving import records to the bottom, compacting import records into list rows, adding a data-version detail route, moving rollback strategy into the detail page, and hiding rollback from operator accounts.
- v3.1.2: Added rollback linked-task strategies so report version rollback can move related tasks to manual review, archive them with audit, or keep current status; added strategy selector on the report page.
- v3.1.1: Added report import-record management, data-version soft rollback, rollback audit records, report-page rollback cards, and rollback health flags.
- v3.1.0: Added standalone inventory and customer-service centers, store-scoped inventory / service task routes, manager operation-module entries, and operation-center UI pages.
- v3.0.9: Added automatic recap candidates after manager evidence approval, recap candidate service and endpoint, log-page recap candidate board, and automatic复盘候选 logs for daily / weekly review.
- v3.0.8: Added structured task evidence submission, manager evidence review, evidence records, review records, task evidence endpoints, and the Todo handling form so tasks are submitted with audit material instead of completed by a bare click.
- v3.0.7: Added alert evidence detail reports with source trace, trigger rule, store responsibility, raw report rows, evidence chain, and frontend entry from latest report alerts.
- v3.0.6: Hardened report data ownership by binding imported report rows, alert events, dashboard summary, report module alerts, and generated warning tasks to store scope; added store_id / store_name field aliases and account-scoped alert APIs.
- v3.0.5: Compacted manager navigation, nested product / competitor / listing / traffic / report operation pages under the manager operation-module hub, added clickable manager module cards, and extended minimal UI cleanup to manager pages.
- v3.0.4: Added minimal UI cleanup, removed explanatory grey microcopy through a global UI layer, changed store owner changes into confirmed next-day migration records, added pending store migrations, and changed owner-side store responsibility changes to require management confirmation.
- v3.0.3: Split operating-unit visibility from store responsibility permissions, added store assignments, scoped operating-unit/product/listing/traffic data by viewer store permissions, redesigned organization responsibility controls, and moved report upload into a separate layout panel.
- v3.0.2: Added report schema preview, field alias mapping, `/api/data/templates`, `/api/data/preview`, `/api/data/import/confirm`, frontend three-step import flow, preview table, and confirm-before-alert behavior.
- v3.0.1: Reworked the report page into a file-first upload flow, moved mock alert generation into a backup demo action, added client-side CSV parsing, improved report upload layout, and truncated long data versions in cards.
- v3.0.0: Added report-driven data snapshots, metric snapshots, alert events, alert-to-task bridge, V3 data summary API, one-click mock report alert import, and frontend alert sync for dashboard/report/product/traffic modules.
- v2.5.1: Added cross-account task lifecycle sync with task events, per-user counters, operator accept action, manager review sync, and recap handoff.
- v2.5.0: Rebuilt the task system into a role-scoped task flow with store permissions, visible roles/users/stores, owner decision tasks, manager dispatch tasks, operator execution tasks, warning-to-operator todo routing, and manager split endpoint.

## Version Rules

- Patch: copy, prompt, template, or wording changes.
- Minor: new module, new mode, new interface, or new runtime config.
- Major: breaking workflow, API contract, schema, or folder migration changes.
