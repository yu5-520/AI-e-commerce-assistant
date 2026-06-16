# Product Changelog

## v2.4.2 - 2026-06-16

### Product Decision
- V2.4.2 restores the operator-side operation modules.
- Product truth: 运营账号不是纯待办执行人，而是被分配店铺权限的店铺经营者。
- 运营能看经营单元、报表、商品、竞品、上新、流量、待办、日志和账号，但数据口径限定在“我负责的店铺”。

### Changed
- Operator navigation now shows: 总览、经营单元、报表、商品、竞品、上新、流量、待办、日志、账号.
- Operator dashboard changed into `我的店铺经营总览`.
- Added assigned-store cards and module entry cards for operator accounts.
- Added `web_demo/operator-dashboard.css`.
- Operator account role copy now clarifies assigned-store scope instead of task-only scope.
- Frontend assets now use `?v=2.4.2`; API and health versions are aligned.

### Product Boundary
- This remains mock scoped-store data.
- Real version should connect ERP / CRM / shop authorization APIs, store-level permission filtering, report-level filtering, product ownership, traffic ownership, and operator-specific task/log APIs.

## v2.4.1 - 2026-06-16

### Product Decision
- V2.4.1 optimizes 店群总管 `今日处理顺序` layout.
- Product truth: 店群总管需要的是调度队列，不是普通卡片列表；功能按钮可以多，但排版必须先服务“第几个处理、何时到期、来源是什么、判断是什么、下一步点哪里”。
- The layout keeps task actions while restoring the stronger schedule-row visual hierarchy.

### Changed
- 店群总管首页和店群任务 / 任务派发 / 运营复核使用统一的调度队列卡片。
- Added row structure: 序号、时间/优先级、主任务、来源、判断、操作.
- Kept actions: 查看详情、拆分 / 派发、进入复核.
- Sorting controls remain, but are visually lighter.
- Frontend assets now use `?v=2.4.1`; API and health versions are aligned.

### Product Boundary
- This remains mock local task state.
- Real version should connect sorting rules, SLA deadline rules, split records, assignment APIs, and Agent task-detail judgment.

## v2.4.0 - 2026-06-16

### Product Decision
- V2.4.0 changes 老板账号 `总览` from task list into business overview.
- Product truth: 老板总览不是任务池，是全局经营首页；老板看经营摘要和决策入口，任务拆分、派发和复核属于店群总管。
- 老板关注事项只进入对应模块查看详情，不做“完成任务”。

### Changed
- Owner dashboard now shows operating metrics: 今日销售额、今日利润、今日订单、库存资金、广告消耗、退款率、待审计问题、待确认复盘.
- Added owner module entry cards: 店群总览、人员总览、供投财务、组织效率、复盘审计.
- Added owner attention items: 周报目标未达标、抖音 ROAS 偏低、拼多多退款率上升、总管复核节奏偏慢.
- Added `web_demo/owner-dashboard.css`.
- Frontend assets now use `?v=2.4.0`; API and health versions are aligned.

### Product Boundary
- This remains mock overview data.
- Real version should connect store metrics, people workload, supply / ad / finance metrics, organization exceptions, and retrospective audit records.

## v2.3.9 - 2026-06-16

- 店群总管 upgraded from a static execution board into an actionable task dispatch workbench.

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
