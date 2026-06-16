# Product Changelog

## v1.5.0 - 2026-06-16

### Product Decision
- V1.5.0 completes the backend module-file split promised after v1.4.1.
- Product truth: each backend module should be maintainable independently, while `src/api/routes/modules/__init__.py` only aggregates routers.

### Changed
- Split the monolithic modular route file into separate backend module files:
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
- `src/api/routes/modules/__init__.py` now only creates the `/api/modules` router and includes each module router.
- Frontend assets now use `?v=1.5.0`; API and health versions are aligned.

### Product Boundary
- This is a backend maintainability refactor, not a new data feature.
- API paths remain the same, so the frontend still calls `/api/modules/*`.
- Mock data and task/log authority remain in `module_data_service.py` and `module_task_service.py` until database persistence is added.

## v1.4.1 - 2026-06-16

### Product Decision
- V1.4.1 closes the broken chain found after v1.4.0: module data, task creation, todo, and log state should come from backend module services, not browser-only state.
- Product truth: frontend localStorage is now a hydrated cache; server-side mock services are the current task/log authority.

### Changed
- Added `src/services/module_data_service.py` as the single backend source for current module Mock data.
- Added `src/services/module_task_service.py` as the server-side mock task/log service.
- Reduced `web_demo/core/mock-data.js` to a minimal fallback shell to avoid maintaining the same Mock ERP / CRM data twice.
- `web_demo/core/api-client.js` now supports task creation, todo completion, pinning, reordering, reset, task refresh, and log refresh through `/api/modules/*`.
- Product, competitor, listing, traffic, and report module task buttons now call backend module endpoints before refreshing local task state.
- Todo page actions now call backend todo endpoints before refreshing task/log state.
- Header badge now shows `服务端接口` or `本地兜底` so API fallback no longer silently hides chain failures.
- Frontend assets now use `?v=1.4.1`; API and health versions are aligned.

### Product Boundary
- This is still in-memory server-side mock persistence, not a production database.
- Server restart will reset demo task/log state.
- Real account roles, permissions, multi-user consistency, and ERP / CRM connectors remain later work.

## v1.4.0 - 2026-06-16

### Product Decision
- V1.4.0 aligns the backend with the v1.3 modular frontend.
- Product truth: one frontend route module should map to one backend module endpoint under `/api/modules/*`.
- The old `/api/business/*` product path is removed from the active backend entry to avoid two competing interface families.

### Changed
- Added modular backend API under `src/api/routes/modules/__init__.py`.
- Added module data endpoints for dashboard, operating unit, report, product, competitor, listing, traffic, todo, and log.
- Added module action endpoints for creating task payloads from product, competitor, listing, traffic, and report modules.
- Added `web_demo/core/api-client.js` as the unified frontend request client.
- `bootstrap.js` now prefetches module data before starting the frontend router.
- `index.html` now loads `api-client.js` and uses `?v=1.4.0`.
- `src/api/main.py` now mounts `modules.router` instead of `business.router`.
- Health now reports `api_entry: /api/modules/*`.

### Removed
- Removed the legacy backend router file `src/api/routes/business.py`.
- Removed active `/api/business/*` routes from the application entrypoint.

### Product Boundary
- This is an interface architecture refactor.
- The modular endpoints still return Mock ERP / CRM product data and task payloads.
- Real server-side task persistence, account roles, permissions, and ERP / CRM connectors remain later work.

## Earlier History

- v1.3.0: Frontend changed from hotfix-script stacking into a modular route-registry structure.
- v1.2.0: Added unified front-end route lifecycle coordinator.
- v1.1.2: Fixed fast module-switch crash introduced by observer-based task bridge binding.
- v1.1.1: Added dedupe identity to task-store tasks.
- v1.1.0: Added unified front-end task store and dynamic module task flow.
- v1.0.24: 首页 became a command-board scheduling view.
- v1.0.0-v1.0.23: Product trunk cleanup and page productization.
