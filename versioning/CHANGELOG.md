# Changelog

## v2.0.0 - 2026-06-16

### Added
- Added `src/services/account_service.py` as the v2 Mock account, role, permission, store-group, and store-scope contract.
- Added `src/api/routes/accounts.py` and mounted `/api/accounts` in `src/api/main.py`.
- Added the front-end `账号` navigation item and `web_demo/modules/account/page.js`.
- Added v2 task collaboration endpoints under `/api/modules/todo`:
  - `POST /api/modules/todo/{task_id}/assign`
  - `POST /api/modules/todo/{task_id}/submit`
  - `POST /api/modules/todo/{task_id}/review`
- Added account-aware task fields: assignee, reviewer, assigner, workflow status, submission note, review note, and workflow timestamps.
- Prepared SQLite schema for v2 account and collaboration persistence: accounts, roles, role permissions, store groups, stores, memberships, assignments, submissions, and reviews.

### Changed
- Cleaned the active architecture around `/api/modules/*` and `/api/accounts` instead of stale product docs pointing at old API contracts.
- FastAPI app version and health version are aligned to `2.0.0`.
- Frontend assets were bumped to `?v=2.0.0`.
- `scripts/smoke_test_api.py` now validates current modular APIs, `/api/accounts`, task reports, and the dispatch / submit / review flow.
- `scripts/check_version_governance.py` now requires `/api/modules` and `/api/accounts` in the active version logs.
- README and product docs now describe the v2 collaboration trunk instead of the earlier single-user task demo.

### Product Engineering Rule
- V2.0 changes the product from a single-user operating dashboard into a light enterprise collaboration skeleton.
- Reports still explain and recommend; tasks now carry ownership and review responsibility.
- Account roles define visibility and task flow, but this version still does not connect real SSO, real tenant billing, or real shop execution.

## v1.6.1 - 2026-06-16

### Added
- Added `createTaskFromReport(module, entityId)` in `web_demo/core/task-actions.js`.
- Candidate report pages now show a primary `加入任务清单` button at the bottom.

### Changed
- Candidate report pages now support the normal operating flow: `查看预警 -> 阅读完整报告 -> 加入任务清单 -> 跳转待办任务位置`.
- `web_demo/modules/task-report/page.js` now creates the correct module task from the report context and jumps to the new active task in 待办.
- Frontend assets were bumped to `?v=1.6.1`.
- FastAPI app version and health version are aligned to `1.6.1`.

### Product Engineering Rule
- A candidate report is not only a read-only explanation page. It is also a task conversion page.
- Operators should not need to return to the source module after reading the full report just to add the same candidate to 待办.

## v1.6.0 - 2026-06-16

### Added
- Added `src/services/task_report_service.py` as the report-generation boundary for task and candidate detail reports.
- Added `src/api/routes/modules/task_report.py` with independent report APIs:
  - `GET /api/modules/task-reports/tasks/{task_id}`
  - `GET /api/modules/task-reports/candidates/{module}/{entity_id}`
- Added `web_demo/modules/task-report/page.js` as the independent detail report page.
- Added report navigation helpers in `web_demo/core/task-actions.js`.
- Added `详情报告` button in 待办 task cards.
- Added `查看预警` / `任务报告` buttons in 商品、竞品、上新、流量、报表 modules.

### Changed
- Existing source-module tasks can now open an independent task report page instead of only jumping to 待办.
- Candidate reports explain why a module item is being warned before it enters 待办.
- Task reports explain why the task exists, what evidence supports it, what the operator should check, and what should be confirmed manually.
- Frontend assets were bumped to `?v=1.6.0`.
- FastAPI app version and health version are aligned to `1.6.0`.

### Product Engineering Rule
- Task detail is now a first-class route, not a small inline note.
- Agent integration should enrich report payloads before human confirmation; Agent should not directly complete tasks or mutate shop data.
- Report snapshots should become part of the log archive when database persistence is added.

## v1.5.3 - 2026-06-16

### Added
- Added source-candidate lifecycle support in `src/services/module_task_service.py`:
  - `pending_candidate`
  - `active_task`
  - `completed_archived`
- Added `visible_candidates()` so source modules can hide completed candidates by default.
- Added completed candidate metadata: `completedTaskId`, `completedTaskStatus`, `candidateArchived`, and `candidateStatus`.

### Changed
- Product, competitor, listing, traffic, and report module APIs now filter out completed source candidates.
- Completing a task now marks its source candidate as `completed_archived`.
- Direct attempts to re-create an already completed candidate are intercepted and logged instead of creating a duplicate task.
- `web_demo/core/api-client.js` now refreshes source module data after task/log state refresh, so module lists release completed work slots after 待办 completion.
- Frontend assets were bumped to `?v=1.5.3`.
- FastAPI app version and health version are aligned to `1.5.3`.

### Product Engineering Rule
- Completed work should leave 待办 and its source module candidate list.
- Completed work belongs in 日志 only until a new signal / new cycle id creates a fresh candidate.
- Source modules are cycle queues, not permanent archives.

## Earlier History

- v1.5.2: Existing-task buttons jump to the matching task card inside 待办.
- v1.5.1: Backend owns task identity and active-task status.
- v1.5.0: Split backend module routes into separate files.
- v1.4.1: Closed the module API chain and moved task/log authority to backend mock services.
- v1.4.0: Added modular backend API routes and removed active `/api/business/*` product path.
- v1.3.0: Added modular frontend route registry and removed legacy hotfix scripts.
- v1.2.0: Added unified front-end route lifecycle coordinator.
- v1.1.2: Fixed module-switch crash caused by global task bridge MutationObserver loop.
- v1.1.1: Added task identity and dedupe keys for same-product same-problem task merging.
- v1.1.0: Added unified front-end task store and dynamic module-driven task flow.
- v1.0.24: Dashboard task board was simplified into a command-board scheduling view with short judgment tags.
- v1.0.0-v1.0.23: Product trunk cleanup and page-level productization.
