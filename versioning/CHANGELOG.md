# Changelog

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
- `bootstrap.js` no longer dynamically loads page modules already loaded by `index.html`, reducing duplicate frontend loading.
- `index.html` now loads normalized report / manager runtime filenames and bumps all static assets to `?v=3.1.4`.
- Removed unused versioned report and manager runtime files.
- FastAPI app version and health version are aligned to `3.1.4`.

### Product Engineering Rule
- Version numbers belong in cache query strings and version files, not long-lived module filenames. Detail pages should read one backend payload rather than assembling business facts from multiple frontend list calls.

## v3.1.3 - 2026-06-17

### Added
- Added `data-version-detail` as a standalone data-version detail route.
- Added compact import-record rows at the bottom of the report page.
- Added permission-based rollback controls: owner / manager / finance can rollback; operator can only view records and details.

### Changed
- Report page hierarchy now prioritizes upload, preview, latest alerts, and report cards before data-version management.
- Import records are moved from the top/middle of the report page to the bottom.
- Import records no longer show rollback strategy directly in the list; rollback strategy moved into the version detail page.
- Report rollback UI assets were bumped to `?v=3.1.3`.
- FastAPI app version and health version are aligned to `3.1.3`.

### Product Engineering Rule
- Import records are audit tools, not the primary report workflow. The report homepage should stay operational, while rollback and strategy controls live in data-version detail.

## v3.1.2 - 2026-06-17

### Added
- Added linked-task strategy handling to `src/services/data_version_service.py`.
- Added `taskStrategy` support to `/api/data/versions/{data_version}/rollback`.
- Added report-page strategy selector for rollback-linked tasks.
- Added V3.1.2 health flags for `review`, `archive`, and `keep` rollback strategies.

### Changed
- Data-version rollback now handles linked tasks instead of only rolling back alert events.
