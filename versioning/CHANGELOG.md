# Changelog

## v2.3.3 - 2026-06-16

### Added
- Added owner-facing `供投财务` content under the existing `profit-budget` route for compatibility.
- Added supply overview data: suppliers, category, cost change, delivery cycle, inventory amount, safety inventory, and state.
- Added traffic overview data: ad spend, ROAS, CPC, conversion, paid orders, natural orders, and state.
- Added finance summary data: sales, gross profit, ad cost, refund cost, logistics cost, platform fee, inventory capital, and net profit.
- Added `web_demo/supply-finance.css` for the supply / traffic / finance table layout.

### Changed
- Owner navigation label changed from `利润预算` to `供投财务`.
- The owner page now explains profit through goods, traffic, and money instead of showing only financial result cards.
- Frontend assets were bumped to `?v=2.3.3`.
- FastAPI app version and health version are aligned to `2.3.3`.

### Product Engineering Rule
- Boss accounts should inspect goods, traffic, and finance together.
- Profit is a result; supply stability, traffic spend, refund cost, logistics cost, platform fee, and inventory capital explain why the result changes.

## v2.3.2 - 2026-06-16

- Owner-side `任务指挥` was repositioned into `人员总览`.

## v2.3.1 - 2026-06-16

- `店群总览` was upgraded into a realtime operations board.

## v2.3.0 - 2026-06-16

- Removed owner `经营驾驶舱` and repositioned `风险中心` into `店群总览`.

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
