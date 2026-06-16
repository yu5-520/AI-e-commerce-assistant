# Product Changelog

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
