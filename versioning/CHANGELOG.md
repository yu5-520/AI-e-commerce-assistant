# Changelog

## v1.5.1 - 2026-06-16

### Added
- Added `src/services/dashboard_service.py` as the dashboard module service boundary.
- Added backend task-state helpers in `module_task_service.py`: `find_open_task_by_key`, `task_state_for_payload`, and `attach_task_state`.
- Product module responses now include backend-generated `suggestedTaskKey`, `activeTaskId`, `activeTaskStatus`, and `hasActiveTask`.
- API badge tooltip now exposes recent fallback failure paths and messages.

### Changed
- `src/api/routes/modules/dashboard.py` now calls `dashboard_service.get_dashboard_summary()` instead of directly depending on `business_view_service`.
- `src/api/routes/modules/product.py` now uses one backend `product_task_payload()` for both product task creation and product list task-state annotation.
- `web_demo/stores/task-store.js` no longer infers risk domain or action type. It now accepts backend task identity as the source of truth.
- `web_demo/core/task-actions.js` now reads product identity from backend-returned task state instead of recalculating it from product fields.
- `web_demo/core/api-client.js` now preserves fallback failure details through `failureSummary()`.
- Frontend assets were bumped to `?v=1.5.1`.
- FastAPI app version and health version are aligned to `1.5.1`.

### Product Engineering Rule
- Backend owns task identity and active-task status.
- Frontend task store is a hydrated cache and should not independently infer business risk/action rules.
- Dashboard should depend on `dashboard_service` as its module service boundary.

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

## v1.4.1 - 2026-06-16

### Added
- Added `src/services/module_data_service.py` as the backend source of truth for current Mock ERP / CRM module data.
- Added `src/services/module_task_service.py` as the server-side mock task/log authority.
- Added server-side task actions for create, merge, complete, pin, reorder, reset, and log creation.
- Added frontend API methods for module task creation, todo completion, pinning, reordering, reset, and task/log refresh.

### Changed
- `src/api/routes/modules/__init__.py` now imports module data from `module_data_service` instead of keeping large duplicated constants inside the route file.
- `GET /api/modules/todo` now returns service-side task state instead of old approval/action-confirmation data.
- `GET /api/modules/log` now returns service-side operation logs.
- Product, competitor, listing, traffic, and report task actions now create tasks on the backend module endpoints first, then hydrate the frontend task store.
- Todo page actions now call backend task endpoints first, then refresh frontend state from `/api/modules/todo` and `/api/modules/log`.
- Frontend `mock-data.js` was reduced to a minimal fallback shell so module demo data is no longer maintained twice.
- Frontend badge now shows whether the UI is using `服务端接口` or `本地兜底`.
- Frontend assets were bumped to `?v=1.4.1`.
- FastAPI app version and health version are aligned to `1.4.1`.

### Product Engineering Rule
- Backend module data is now the current source of truth for module lists.
- Backend task/log service is now the current source of truth for task and log state.
- Frontend localStorage remains a hydrated cache, not the product authority.
- This is still mock server memory, not database persistence; account roles and multi-user consistency still require a later persistence layer.

## Earlier History

- v1.4.0: Added modular backend API routes and removed active `/api/business/*` product path.
- v1.3.0: Added modular frontend route registry and removed legacy hotfix scripts.
- v1.2.0: Added unified front-end route lifecycle coordinator.
- v1.1.2: Fixed module-switch crash caused by global task bridge MutationObserver loop.
- v1.1.1: Added task identity and dedupe keys for same-product same-problem task merging.
- v1.1.0: Added unified front-end task store and dynamic module-driven task flow.
- v1.0.24: Dashboard task board was simplified into a command-board scheduling view with short judgment tags.
- v1.0.0-v1.0.23: Product trunk cleanup and page-level productization.
