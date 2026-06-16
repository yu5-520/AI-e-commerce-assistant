# Product Changelog

## v2.3.5 - 2026-06-16

### Product Decision
- V2.3.5 changes owner-side `复核审计` into `复盘审计`.
- Product truth: 老板不常因为单个店铺短期波动直接下任务，老板通常通过日报、周报、月报复盘和审计结论确定下周 / 下月任务。
- `复盘审计`不是单条任务日志，而是周期复盘接收、运行失误审查和下周期任务生成入口。

### Changed
- Owner navigation label changed from `复核审计` to `复盘审计`.
- Added retrospective intake: 日报、周报、月报、专项复盘.
- Added audit issue list: 周报未达标、ROI 不达标、退款率上升、复核延迟.
- Added next-cycle task drafts: 下周任务、下月任务、责任主管、拆分方向、优先级、下发状态.
- Frontend assets now use `?v=2.3.5`; API and health versions are aligned.

### Product Boundary
- This remains mock retrospective data.
- Real version should connect daily / weekly / monthly report submissions, task timeout records, KPI target rules, and task-generation approvals.

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
