# Product Changelog

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
- Product task creation and product list task-state annotation now share the same backend `product_task_payload()` rule.
- Traffic task creation and traffic list task-state annotation now share the same backend `traffic_task_payload()` rule.
- Frontend `task-store.js` no longer infers risk domain or action type; it accepts backend identity fields as source of truth.
- Frontend product and traffic button state now read backend-provided task identity rather than recalculating from page fields.
- Todo execution queue now renders `listActiveTasks()` so completed tasks immediately leave 待办.
- API badge tooltip now exposes recent fallback failures so server chain breaks are easier to find.
- Frontend assets now use `?v=1.5.1`; API and health versions are aligned.

### Product Boundary
- Server task/log state is still in-memory mock persistence.
- `business_view_service.py` remains available for dashboard workflow summary while the deeper workflow service is migrated later.
- Database persistence, account roles, and multi-user consistency remain later work.

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

## Earlier History

- v1.4.1: Closed the module API chain and moved task/log authority to backend mock services.
- v1.4.0: Backend aligned with modular frontend and removed active `/api/business/*` routes.
- v1.3.0: Frontend changed from hotfix-script stacking into a modular route-registry structure.
- v1.2.0: Added unified front-end route lifecycle coordinator.
- v1.1.2: Fixed fast module-switch crash introduced by observer-based task bridge binding.
- v1.1.1: Added dedupe identity to task-store tasks.
- v1.1.0: Added unified front-end task store and dynamic module task flow.
- v1.0.24: 首页 became a command-board scheduling view.
- v1.0.0-v1.0.23: Product trunk cleanup and page productization.
