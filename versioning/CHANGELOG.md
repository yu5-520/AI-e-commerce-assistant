# Changelog

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
