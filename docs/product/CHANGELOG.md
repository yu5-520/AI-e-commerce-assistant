# Product Changelog

## v1.6.0 - 2026-06-16

### Product Decision
- V1.6.0 adds an independent detail report page instead of an inline drawer.
- Product truth: tasks need decision context, not just execution buttons. A task report explains why the warning exists, what evidence supports it, and how operators should handle it.

### Changed
- Added `src/services/task_report_service.py` as the report-generation boundary and future Agent insertion point.
- Added task report APIs:
  - `GET /api/modules/task-reports/tasks/{task_id}`
  - `GET /api/modules/task-reports/candidates/{module}/{entity_id}`
- Added `web_demo/modules/task-report/page.js` as an independent detail page.
- 待办 cards now include `详情报告`.
- 商品、竞品、上新、流量、报表 now include `查看预警` before task creation and `任务报告` after the task enters 待办.
- Existing report content includes warning summary, evidence, AI assessment, suggested actions, operation checklist, needed data, human decision points, next step, and Agent boundary.
- Frontend assets now use `?v=1.6.0`; API and health versions are aligned.

### Product Boundary
- This is still template-based report generation from current Mock ERP / CRM data.
- Agent is not yet connected; the report service is the reserved insertion point.
- Agent should enrich reports and checklist suggestions, not directly complete tasks or mutate ERP / CRM / shop data.

## v1.5.3 - 2026-06-16

### Product Decision
- V1.5.3 changes completed-task behavior from `completed -> can be added again` to `completed -> archived from source modules`.
- Product truth: source modules are current-cycle queues. Once a task is completed, it frees the source module position and belongs only in 日志 until a new signal / new cycle enters.

### Changed
- Added source-candidate lifecycle state in `module_task_service.py`: `pending_candidate`, `active_task`, and `completed_archived`.
- Product, competitor, listing, traffic, and report APIs now hide completed candidates from their source module lists.
- Completing a task now marks the source candidate as `completed_archived` and writes a log entry that the source module slot has been released.
- Direct attempts to re-create an already completed candidate are intercepted and logged instead of creating a duplicate task.
- `web_demo/core/api-client.js` now refreshes source module data after task/log state changes, so completed work disappears from related modules after 待办 completion.
- Frontend assets now use `?v=1.5.3`; API and health versions are aligned.

### Product Boundary
- This is still in-memory server-side mock persistence.
- Completion archive is based on the current dedupe key; a future new signal should use a new cycle id / source event to re-enter the source module queue.
- Completed tasks remain visible through 日志, not through 待办 or source modules.

## Earlier History

- v1.5.2: Existing-task buttons jump to the matching task card inside 待办.
- v1.5.1: Backend owns task identity and active-task status.
- v1.5.0: Backend module-file split.
- v1.4.1: Closed the module API chain and moved task/log authority to backend mock services.
- v1.4.0: Backend aligned with modular frontend and removed active `/api/business/*` routes.
- v1.3.0: Frontend changed from hotfix-script stacking into a modular route-registry structure.
- v1.2.0: Added unified front-end route lifecycle coordinator.
- v1.1.2: Fixed fast module-switch crash introduced by observer-based task bridge binding.
