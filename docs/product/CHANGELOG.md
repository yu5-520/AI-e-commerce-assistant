# Product Changelog

## v2.3.6 - 2026-06-16

### Product Decision
- V2.3.6 changes `复盘审计` from table-style rows into summary-first expandable cards.
- Product truth: 日报、周报、月报、审计问题和任务草案都需要展开详情层，后续才能承接 Agent 的信息检索、证据判断和任务生成依据。
- 老板第一眼看摘要，需要判断时再展开，不应该被宽表格和长文本挤压。

### Changed
- 周期复盘接收改为可展开卡片：每条复盘可展开目标、实际、达成率、复盘要点和 Agent 预留判断。
- 审计问题清单改为可展开卡片：每条问题可展开审计证据和 Agent 判断项。
- 下周期任务草案改为可展开卡片：每条任务可展开目标、拆分方向和后续按钮入口。
- Added `web_demo/review-audit.css` for expandable retrospective layout.
- Frontend assets now use `?v=2.3.6`; API and health versions are aligned.

### Product Boundary
- This remains mock retrospective data.
- Real version should connect daily / weekly / monthly report submissions, task timeout records, KPI target rules, Agent evidence retrieval, and task-generation approvals.

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
