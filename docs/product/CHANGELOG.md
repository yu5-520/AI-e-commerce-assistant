# Product Changelog

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

## v1.5.2 - 2026-06-16

### Product Decision
- V1.5.2 unifies the behavior of `已在任务清单` buttons across 商品、竞品、上新、流量、报表.
- Product truth: if a task already exists, the module should navigate to the exact active task in 待办 instead of trying to create or merge the same task again.

### Changed
- Added router state support so a module can navigate to `business-actions` with a target `focusTaskId`.
- Added shared task navigation helpers in `web_demo/core/task-actions.js`.
- Product, competitor, listing, traffic, and report modules now render existing-task buttons as `已在任务清单`.
- Clicking `已在任务清单` now jumps to the matching task card in 待办 and briefly highlights it.
- Competitor, listing, and report backend module responses now include task-state identity fields, matching product and traffic behavior.
- Todo cards now expose task ids through `data-task-card` for focused navigation.
- Frontend assets now use `?v=1.5.2`; API and health versions are aligned.

### Product Boundary
- This does not add database persistence.
- Completed tasks still disappear from 待办 and remain in 日志.
- Existing-task navigation only works for active tasks; completed tasks correctly restore the module button to `加入任务清单`.

## v1.5.1 - 2026-06-16

### Product Decision
- V1.5.1 removes the remaining task-identity duplication and closes the dashboard service boundary.
- Product truth: backend owns task identity, active-task state, and dashboard service composition; frontend only hydrates and displays.
- 待办只展示未完成任务；完成后从执行队列消失，只保留日志复盘。

### Changed
- Added `src/services/dashboard_service.py` as the dashboard module service boundary.
- Dashboard route now calls `dashboard_service.get_dashboard_summary()` instead of directly calling old business view helpers.
- Added backend task-state helpers in `module_task_service.py` for open-task lookup and task-state annotation.
- Product and traffic list responses now include `suggestedTaskKey`, `activeTaskId`, `activeTaskStatus`, and `hasActiveTask` from the backend.
- Todo execution queue now renders `listActiveTasks()` so completed tasks immediately leave 待办.
- API badge tooltip now exposes recent fallback failures so server chain breaks are easier to find.
- Frontend assets now use `?v=1.5.1`; API and health versions are aligned.

### Product Boundary
- Server task/log state is still in-memory mock persistence.
- `business_view_service.py` remains available for dashboard workflow summary while the deeper workflow service is migrated later.
- Database persistence, account roles, and multi-user consistency remain later work.

## Earlier History

- v1.5.0: Backend module-file split.
- v1.4.1: Closed the module API chain and moved task/log authority to backend mock services.
- v1.4.0: Backend aligned with modular frontend and removed active `/api/business/*` routes.
- v1.3.0: Frontend changed from hotfix-script stacking into a modular route-registry structure.
- v1.2.0: Added unified front-end route lifecycle coordinator.
- v1.1.2: Fixed fast module-switch crash introduced by observer-based task bridge binding.
