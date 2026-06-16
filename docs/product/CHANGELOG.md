# Product Changelog

## v2.5.0 - 2026-06-16

### Product Decision
- V2.5.0 rebuilds the task system from a single-account todo list into a role-permission-driven task flow.
- Product truth: 任务不是单个账号的待办列表，而是围绕店铺权限、角色职责和复盘链路流转的经营对象。
- 老板看决策任务，总管看调度任务，运营看执行任务。
- 商品、竞品、上新、流量等模块预警不进入全局待办，而是根据店铺归属和账号权限生成可见任务。

### Changed
- Task payloads now include role and permission fields: `taskLayer`, `sourceType`, `ownerRole`, `parentTaskId`, `childTaskIds`, `storeIds`, `storeGroupId`, `visibleRoleIds`, `visibleUserIds`, `visibleStoreIds`, `recapTarget`, `agentJudgment`.
- Product / competitor / listing / traffic warnings are routed to the operator responsible for the affected store and remain visible to the store-group manager.
- Owner account no longer receives ordinary operator execution tasks in the task pool.
- Manager account sees group dispatch, split, review, warning, and retrospective tasks.
- Operator account sees assigned tasks and warning tasks inside its authorized store scope.
- Finance account sees finance / report / ROI / inventory related tasks.
- Added `POST /api/modules/todo/{task_id}/split` for manager split flow.
- Client fallback task store also respects role / user / store scope.
- Frontend assets now use `?v=2.5.0`; API and health versions are aligned.

### Product Boundary
- This remains in-memory mock task routing.
- Real version should move the same rules into database-backed task tables, store permission tables, task-source records, child-task records, assignment records, review records, and Agent evidence snapshots.

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

- Optimized 店群总管 `今日处理顺序` into schedule-row dispatch queue layout.

## v2.4.0 - 2026-06-16

- Changed 老板账号 `总览` from task list into business overview.

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
