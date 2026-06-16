# Product Changelog

## v2.3.9 - 2026-06-16

### Product Decision
- V2.3.9 upgrades 店群总管 from a static execution board into an actionable task dispatch workbench.
- Product truth: 店群总管必须能按时间、优先级、来源、状态排序任务，并能从任务卡直接进入详情、拆分、派发和复核。
- 任务详情页是后续 Agent 判断的承接层，不是普通列表行。

### Changed
- Added sort controls for manager task list: 按时间、按优先级、按来源、按状态.
- Added task actions on manager cards: 查看详情、拆分任务、派发运营.
- Added `manager-task-detail` route with task source, source report, impact scope, data evidence, Agent judgment placeholders, and suggested split actions.
- Added mock task state transitions: 待拆分 → 待派发 → 已派发 → 待复核 → 已归档.
- Manager dashboard task cards can now jump to task detail, dispatch, or review.
- Frontend assets now use `?v=2.3.9`; API and health versions are aligned.

### Product Boundary
- This remains local mock task state.
- Real version should connect task splitting records, operator assignment APIs, task detail reports, Agent evidence retrieval, review records, and retrospective submission APIs.

## v2.3.8 - 2026-06-16

- 店群总管 side changed into execution management workflow.

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
