# Changelog

## v2.3.1 - 2026-06-16

### Added
- Added a realtime sync status strip to `店群总览`, including ERP time, platform sync states, delay marker, and active task count.
- Added platform live cards with order, sales, profit, comment, progress, and sync status indicators.
- Added a horizontal store operation table for store, platform, product count, active products, orders, sales, profit, comments, bad comments, refund rate, inventory amount, pending tasks, and state.
- Added trend chips for order, sales, profit, and refund-related metrics.

### Changed
- Fixed the store detail layout issue where long card text squeezed store names into vertical text.
- Replaced long sentence cards with a data-table board so owners can compare stores horizontally.
- Frontend assets were bumped to `?v=2.3.1`.
- FastAPI app version and health version are aligned to `2.3.1`.

### Product Engineering Rule
- `店群总览` should look and behave like a realtime operations board.
- It should show live business facts first; exception analysis and risk tasks should drill down from field states rather than dominate the first screen.

## v2.3.0 - 2026-06-16

### Added
- Added owner-facing `店群总览` route at `store-overview`.
- Added platform and store-level summary cards for platforms, store count, online products, orders, sales, profit, comments, refund rate, inventory amount, and pending tasks.

### Changed
- Removed the redundant owner `经营驾驶舱` navigation route.
- Replaced owner `风险中心` with `店群总览` so the owner first sees the business operating board instead of direct risk conclusions.
- `web_demo/modules/executive/page.js` now exports `StoreOverviewPage` and no longer exports `ExecutiveCockpitPage` / `RiskCenterPage`.
- Owner visible modules now use `store-overview`, `task-command`, `profit-budget`, `org-efficiency`, `review-audit`, `accounts`, and `role-console`.
- Frontend assets were bumped to `?v=2.3.0`.
- FastAPI app version and health version are aligned to `2.3.0`.

### Product Engineering Rule
- Boss accounts should see the operating board before risk conclusions.
- Risk is not the first layer; it should grow out of platform, store, product, order, sales, profit, comment, refund, inventory, and task data.
- First-line operation modules remain evidence and execution layers for manager / operator roles.

## v2.2.0 - 2026-06-16

### Added
- Added executive-level frontend modules for 老板账号: `经营驾驶舱`, `风险中心`, `任务指挥`, `利润预算`, `组织效率`, and `复核审计`.
- Added `web_demo/modules/executive/page.js` to hold the owner-facing decision modules.
- Added a lightweight `角色权限控制台` route for mock role promotion/demotion, store-scope assignment, and permission template changes.
- Added mock account management API actions under `/api/accounts`:
  - `POST /api/accounts/users/{user_id}/role`
  - `POST /api/accounts/users/{user_id}/stores`
  - `POST /api/accounts/roles/{role_id}/permissions`

### Changed
- Owner navigation no longer exposes the first-line operation modules as daily function bars. 商品、竞品、上新、流量 remain data-source and execution modules for 总管 / 运营.
- The active product route set still uses `/api/modules/*` plus `/api/accounts`, but owner-facing routes now sit at the frontend decision layer.
- Account page was slimmed into an account summary and role-console entry instead of a large permission explanation wall.
- Frontend assets were bumped to `?v=2.2.0`.
- FastAPI app version and health version are aligned to `2.2.0`.

### Product Engineering Rule
- Boss accounts own cross-module decision power, not first-line operation workbenches.
- Product/competitor/listing/traffic modules are evidence sources for executive views, not owner navigation tabs.
- Role management belongs in a control console, not in the normal account summary page.

## v2.1.0 - 2026-06-16

### Added
- Added global mock account switching through `X-Mock-User-Id` and the topbar account selector.
- Added role-based account context in `src/services/account_service.py`: data scope, visible modules, allowed actions, hidden fields, and insight depth.
- Added productized permission labels so the UI shows Chinese permission names instead of raw engineering ids.
- Added role-aware task filtering and action hints in `src/services/module_task_service.py`.
- Added role-based report insight depth in `src/services/task_report_service.py`.

### Changed
- Frontend assets were bumped to `?v=2.1.0`.
- FastAPI app version and health version are aligned to `2.1.0`.
- 账号 page now changes content according to the selected role.
- 待办 page now shows different task ranges and buttons for 老板、店群总管、运营、数据 / 财务、只读观察.
- Task reports now translate the same warning into different role views: strategy, team management, execution checklist, finance risk, or summary only.

## v2.0.0 - 2026-06-16

### Added
- Added `src/services/account_service.py` as the v2 Mock account, role, permission, store-group, and store-scope contract.
- Added `src/api/routes/accounts.py` and mounted `/api/accounts` in `src/api/main.py`.
- Added the front-end `账号` navigation item and `web_demo/modules/account/page.js`.
- Added v2 task collaboration endpoints under `/api/modules/todo`.
- Prepared SQLite schema for v2 account and collaboration persistence.

### Changed
- Cleaned the active architecture around `/api/modules/*` and `/api/accounts` instead of stale product docs pointing at old API contracts.
- README and product docs now describe the v2 collaboration trunk instead of the earlier single-user task demo.

## Earlier History

- v1.6.1: Candidate report pages include `加入任务清单` and jump to the matching 待办 task.
- v1.6.0: Added independent task detail report pages and candidate report APIs.
- v1.5.3: Added source-candidate lifecycle archiving.
- v1.5.2: Existing-task buttons jump to the matching task card inside 待办.
- v1.5.1: Backend owns task identity and active-task status.
