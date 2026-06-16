# Changelog

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

## v1.5.2 - 2026-06-16

### Added
- Added route state support in `web_demo/core/router.js` so module pages can navigate to 待办 with a target task id.
- Added shared frontend helpers in `web_demo/core/task-actions.js` for existing-task lookup and task-focus navigation.
- Competitor, listing, and report backend module responses now include backend-generated `suggestedTaskKey`, `activeTaskId`, `activeTaskStatus`, and `hasActiveTask`.

### Changed
- Product, competitor, listing, traffic, and report module buttons now use the same behavior:
  - no active task: show `加入任务清单` or the module-specific create label.
  - active task exists: show `已在任务清单`.
  - clicking `已在任务清单`: jump to the matching task card inside 待办.
- Todo cards now expose `data-task-card` and scroll/highlight when opened from a module.
- Frontend assets were bumped to `?v=1.5.2`.
- FastAPI app version and health version are aligned to `1.5.2`.

### Product Engineering Rule
- Existing-task buttons should route to the active task position instead of re-creating or re-merging the same task.
- All task-source modules must use backend task identity and the hydrated active task store to decide button state.

## v1.5.1 - 2026-06-16

### Added
- Added `src/services/dashboard_service.py` as the dashboard module service boundary.
- Added backend task-state helpers in `module_task_service.py`: `find_open_task_by_key`, `task_state_for_payload`, and `attach_task_state`.
- Product and traffic module responses now include backend-generated `suggestedTaskKey`, `activeTaskId`, `activeTaskStatus`, and `hasActiveTask`.
- API badge tooltip now exposes recent fallback failure paths and messages.

### Changed
- `src/api/routes/modules/dashboard.py` now calls `dashboard_service.get_dashboard_summary()` instead of directly depending on `business_view_service`.
- `src/api/routes/modules/product.py` now uses one backend `product_task_payload()` for both product task creation and product list task-state annotation.
- `src/api/routes/modules/traffic.py` now uses one backend `traffic_task_payload()` for both traffic task creation and traffic list task-state annotation.
- `web_demo/modules/todo/page.js` now renders only active tasks in the execution queue; completed tasks disappear from 待办 and remain available through 日志.
- `web_demo/stores/task-store.js` no longer infers risk domain or action type. It now accepts backend task identity as the source of truth.
- `web_demo/core/task-actions.js` now reads product identity from backend-returned task state instead of recalculating it from product fields.
- `web_demo/core/api-client.js` now preserves fallback failure details through `failureSummary()`.
- Frontend assets were bumped to `?v=1.5.1`.
- FastAPI app version and health version are aligned to `1.5.1`.

### Product Engineering Rule
- Backend owns task identity and active-task status.
- Frontend task store is a hydrated cache and should not independently infer business risk/action rules.
- Dashboard should depend on `dashboard_service` as its module service boundary.
- 待办只展示未完成任务；完成后的任务只保留日志复盘，不继续占用执行队列。

## Earlier History

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
