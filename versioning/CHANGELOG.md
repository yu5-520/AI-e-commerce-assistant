# Changelog

## v2.3.2 - 2026-06-16

### Added
- Added owner-facing `人员总览` content under the existing owner command route for compatibility.
- Added employee realtime status cards for 店群总管、运营 A、运营 B、数据财务.
- Added a personnel-task mapping table with role, state, current tasks, today's completed tasks, pending assignment, pending review, returns, timeout count, average handling time, workload, and last action.
- Added `web_demo/people-overview.css` for the personnel table layout.

### Changed
- Owner navigation label changed from `任务指挥` to `人员总览`.
- The owner page now looks at task distribution across people instead of listing individual tasks first.
- FastAPI app version and health version are aligned to `2.3.2`.

### Product Engineering Rule
- Boss accounts should see who is carrying the work, not micromanage every task row.
- Detailed dispatch and review remain manager / operator workflow responsibilities.

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
- Owner visible modules now use `store-overview`, `task-command`, `profit-budget`, `org-efficiency`, `review-audit`, `accounts`, and `role-console`.
- Frontend assets were bumped to `?v=2.3.0`.
- FastAPI app version and health version are aligned to `2.3.0`.

## v2.2.0 - 2026-06-16

- Refactored owner navigation from first-line operation modules into executive modules and added the role permission console.

## v2.1.0 - 2026-06-16

- Added global mock account switching and role-based task visibility.

## v2.0.0 - 2026-06-16

- Added `/api/accounts` and upgraded the task pool into dispatch / submit / review collaboration flow.

## Earlier History

- v1.6.1: Candidate report pages include `加入任务清单` and jump to the matching 待办 task.
- v1.6.0: Added independent task detail report pages and candidate report APIs.
- v1.5.3: Added source-candidate lifecycle archiving.
- v1.5.2: Existing-task buttons jump to the matching task card inside 待办.
- v1.5.1: Backend owns task identity and active-task status.
