# Product Changelog

## v2.3.8 - 2026-06-16

### Product Decision
- V2.3.8 updates the 店群总管 side after the owner-side modules were rebuilt.
- Product truth: 老板定方向和周期任务；店群总管承接任务、拆分派发、复核运营、提交复盘。
- 店群总管不是另一个老板，也不是普通运营；它是老板任务和一线运营之间的执行管理层。

### Changed
- Manager navigation changed to: 总览、店群任务、任务派发、运营复核、经营模块、复盘提交、数据报表、账号.
- Manager dashboard changed into 店群执行总览.
- 商品、竞品、上新、流量 no longer appear as scattered manager-side first-level tabs; they are grouped into 经营模块.
- Added manager-specific pages for task intake, dispatch, review, operation modules, retrospective submission, and data reports.
- Added `web_demo/modules/manager/page.js` and `web_demo/manager-console.css`.
- Frontend assets now use `?v=2.3.8`; API and health versions are aligned.

### Product Boundary
- This remains mock manager workflow data.
- Real version should connect owner retrospective task drafts, assignment records, operator submissions, review outcomes, and daily / weekly / monthly report submission APIs.

## v2.3.7 - 2026-06-16

- `账号` changed into a basic account center.

## v2.3.6 - 2026-06-16

- `复盘审计` changed from table-style rows into summary-first expandable cards.

## v2.3.5 - 2026-06-16

- Owner-side `复核审计` changed into `复盘审计`.

## v2.3.4 - 2026-06-16

- Owner-side `组织效率` changed into organization governance console.

## v2.3.3 - 2026-06-16

- Owner-side `利润预算` changed into `供投财务`.

## v2.3.2 - 2026-06-16

- Owner-side `任务指挥` changed into `人员总览`.

## v2.3.1 - 2026-06-16

- `店群总览` was upgraded into a realtime business operations board.

## v2.3.0 - 2026-06-16

- Removed owner `经营驾驶舱` and repositioned `风险中心` into `店群总览`.

## v2.2.0 - 2026-06-16

- Separated owner decision navigation from first-line operation navigation.

## v2.1.0 - 2026-06-16

- Added global account switching and role-based task/report views.

## v2.0.0 - 2026-06-16

- Added account roles, permissions, and dispatch / submit / review collaboration flow.

## Earlier History

- v1.6.1: Candidate report pages include `加入任务清单`.
- v1.6.0: Added independent detail reports.
- v1.5.3: Completed tasks archive their source candidates.
- v1.5.2: Existing-task buttons jump to the matching task card inside 待办.
- v1.5.1: Backend owns task identity and active-task status.
