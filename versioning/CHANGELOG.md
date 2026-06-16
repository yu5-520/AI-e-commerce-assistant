# Changelog

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
- `web_demo/modules/traffic/page.js` now shows `已在任务清单` when the hydrated task store contains the active backend task.
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

## v1.5.0 - 2026-06-16

### Added
- Added split backend route files under `src/api/routes/modules/`:
  - `dashboard.py`
  - `operating_unit.py`
  - `product.py`
  - `competitor.py`
  - `listing.py`
  - `traffic.py`
  - `report.py`
  - `todo.py`
  - `log.py`
  - `common.py`

### Changed
- `src/api/routes/modules/__init__.py` is now an aggregator only. It creates the shared `/api/modules` router and includes each module router.
- Dashboard, operating unit, product, competitor, listing, traffic, report, todo, and log APIs now each live in their own route file.
- Frontend assets were bumped to `?v=1.5.0`.
- FastAPI app version and health version are aligned to `1.5.0`.

### Product Engineering Rule
- New backend module endpoints should be added inside their own file under `src/api/routes/modules/`.
- `__init__.py` should remain a router aggregator, not a business logic file.
- Route files should call services and return module data; they should not own long-lived business data constants or task state.

## Earlier History

- v1.4.1: Closed the module API chain and moved task/log authority to backend mock services.
- v1.4.0: Added modular backend API routes and removed active `/api/business/*` product path.
- v1.3.0: Added modular frontend route registry and removed legacy hotfix scripts.
- v1.2.0: Added unified front-end route lifecycle coordinator.
- v1.1.2: Fixed module-switch crash caused by global task bridge MutationObserver loop.
- v1.1.1: Added task identity and dedupe keys for same-product same-problem task merging.
- v1.1.0: Added unified front-end task store and dynamic module-driven task flow.
- v1.0.24: Dashboard task board was simplified into a command-board scheduling view with short judgment tags.
- v1.0.0-v1.0.23: Product trunk cleanup and page-level productization.
