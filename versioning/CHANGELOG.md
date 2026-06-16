# Changelog

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

## v1.4.0 - 2026-06-16

### Added
- Added modular backend API routes under `src/api/routes/modules/__init__.py`.
- Added module endpoints aligned to the frontend route registry:
  - `GET /api/modules/dashboard`
  - `GET /api/modules/operating-unit`
  - `GET /api/modules/product`
  - `GET /api/modules/competitor`
  - `GET /api/modules/listing`
  - `GET /api/modules/traffic`
  - `GET /api/modules/report`
  - `GET /api/modules/report/{report_id}`
  - `GET /api/modules/todo`
  - `GET /api/modules/log`
- Added module action endpoints for product, competitor, listing, traffic, report, and todo task completion.
- Added `web_demo/core/api-client.js` to centralize frontend requests to `/api/modules/*`.

### Changed
- `src/api/main.py` now mounts `modules.router` instead of the old `business.router`.
- `web_demo/index.html` now loads `api-client.js` and uses `?v=1.4.0` frontend assets.
- `web_demo/bootstrap.js` now prefetches modular backend data before starting the router.
- Health now reports `version=1.4.0` and `api_entry=/api/modules/*`.

### Removed
- Removed legacy backend compatibility router: `src/api/routes/business.py`.
- Removed active `/api/business/*` product path from `src/api/main.py`.

### Product Engineering Rule
- Frontend module routes and backend module routes should now move together.
- New module data should enter through `/api/modules/<module>`.
- Shared frontend request logic belongs in `web_demo/core/api-client.js`.
- The old `/api/business/*` interface family should not be reintroduced unless explicitly needed as a compatibility wrapper.

## v1.3.0 - 2026-06-16

### Added
- Added modular frontend structure: `web_demo/core/*`, `web_demo/stores/task-store.js`, `web_demo/modules/*/page.js`, and `web_demo/bootstrap.js`.
- Added page modules for dashboard, operating unit, report, product, competitor, listing, traffic, todo, and log routes.
- Added a route registry so pages register themselves through `AppRouter.register(page)` and render through one router lifecycle.

### Changed
- `web_demo/index.html` now loads only the modular frontend entry chain and uses `?v=1.3.0`.
- `task-store` moved into `web_demo/stores/task-store.js` while keeping `window.OPERATION_TASK_STORE` compatibility.
- Task generation moved from global DOM bridge behavior into `web_demo/core/task-actions.js` and module-local event binding.
- FastAPI app version and health version are aligned to `1.3.0`.

### Removed
- Removed legacy root task store, legacy app router, temporary lifecycle shim, page hotfix scripts, and global task bridge.

### Product Engineering Rule
- New frontend features should be added as route modules under `web_demo/modules/<name>/page.js`.
- Shared state belongs in `web_demo/stores/`.
- Shared page shell and routing logic belongs in `web_demo/core/`.
- Modules must not own global `hashchange` listeners or global `MutationObserver` loops.
- Each module owns its own `render / mount / unmount` boundary through the router context.

## Earlier History

- v1.2.0: Added unified front-end route lifecycle coordinator.
- v1.1.2: Fixed module-switch crash caused by global task bridge MutationObserver loop.
- v1.1.1: Added task identity and dedupe keys for same-product same-problem task merging.
- v1.1.0: Added unified front-end task store and dynamic module-driven task flow.
- v1.0.24: Dashboard task board was simplified into a command-board scheduling view with short judgment tags.
- v1.0.0-v1.0.23: Product trunk cleanup and page-level productization.
