# Changelog

## v2.4.2 - 2026-06-16

### Added
- Added operator-specific scoped store operation dashboard.
- Added `web_demo/operator-dashboard.css` for operator store cards and operation module entry cards.
- Added operator dashboard sections for assigned stores, authorized operation modules, and own pending tasks.

### Changed
- Restored operator-side navigation to: 总览、经营单元、报表、商品、竞品、上新、流量、待办、日志、账号.
- Operator role is no longer treated as a pure task-only executor.
- Operator modules are framed around assigned store permissions rather than company-wide visibility.
- Frontend assets were bumped to `?v=2.4.2`.
- FastAPI app version and health version are aligned to `2.4.2`.

### Product Engineering Rule
- 运营账号不是去掉经营模块，而是把经营模块限定在“我负责的店铺范围内”。
- 老板看全部经营结果；店群总管看店群执行调度；运营看被分配店铺的经营、报表、商品、竞品、上新、流量、待办和日志。

## v2.4.1 - 2026-06-16

### Changed
- Optimized the store-group manager `今日处理顺序` and task-list layout.
- Restored the schedule-style dispatch row: rank number, time / priority block, main task area, source block, judgment block, and right-side action buttons.
- Kept the V2.3.9 task actions: 查看详情、拆分 / 派发、进入复核.
- Made sorting controls lighter so they do not visually overpower the task queue.
- Frontend assets were bumped to `?v=2.4.1`.
- FastAPI app version and health version are aligned to `2.4.1`.

### Product Engineering Rule
- 店群总管需要的是调度队列，不是普通卡片列表。
- 任务动作要保留，但视觉骨架必须先服务“处理顺序”。

## v2.4.0 - 2026-06-16

### Added
- Added owner-specific business overview dashboard.
- Added owner operating metrics: sales, profit, orders, inventory capital, ad spend, refund rate, audit issues, and retrospective confirmations.
- Added owner module entry cards for 店群总览、人员总览、供投财务、组织效率、复盘审计.
- Added owner attention items with detail-entry buttons instead of task-completion actions.
- Added `web_demo/owner-dashboard.css` for owner dashboard layout.

### Changed
- Owner `总览` no longer shows the execution-layer task list.
- Task completion / 待办 actions remain for manager / operator contexts, not owner overview.
- Frontend assets were bumped to `?v=2.4.0`.
- FastAPI app version and health version are aligned to `2.4.0`.

### Product Engineering Rule
- 老板总览不是任务池，是全局经营首页。
- 老板看经营摘要和决策入口；任务拆分、派发、复核属于店群总管。

## v2.3.9 - 2026-06-16

- Added manager task sorting by time, priority, source, and status.
- Added manager task detail route `manager-task-detail` with source report, impact scope, evidence, Agent judgment placeholders, and suggested split actions.
- Added task card actions: 查看详情、拆分任务、派发运营.
- Added mock state transitions for manager tasks: 待拆分 → 待派发 → 已派发 → 待复核 → 已归档.

## v2.3.8 - 2026-06-16

- Added manager-specific execution pages: `店群任务`, `任务派发`, `运营复核`, `经营模块`, `复盘提交`, and `数据报表`.
- Manager role now uses a store-group execution management flow.

## v2.3.7 - 2026-06-16

- `账号` was simplified into a basic account center.

## v2.3.6 - 2026-06-16

- `复盘审计` changed from wide tables into expandable retrospective cards.

## v2.3.5 - 2026-06-16

- Rebuilt owner-facing `复核审计` into `复盘审计`.

## v2.3.4 - 2026-06-16

- Rebuilt owner-facing `组织效率` into an organization governance console.

## v2.3.3 - 2026-06-16

- Rebuilt owner `利润预算` into `供投财务`, combining supply, traffic, and finance views.

## v2.3.2 - 2026-06-16

- Owner-side `任务指挥` was repositioned into `人员总览`.

## v2.3.1 - 2026-06-16

- `店群总览` was upgraded into a realtime operations board.

## v2.3.0 - 2026-06-16

- Removed owner `经营驾驶舱` and repositioned `风险中心` into `店群总览`.

## v2.2.0 - 2026-06-16

- Refactored owner navigation from first-line operation modules into executive modules and added the role permission console.

## v2.1.0 - 2026-06-16

- Added global account switching and role-based task visibility.

## v2.0.0 - 2026-06-16

- Added `/api/accounts` and upgraded the task pool into dispatch / submit / review collaboration flow.

## Earlier History

- v1.6.1: Candidate report pages include `加入任务清单` and jump to the matching 待办 task.
- v1.6.0: Added independent task detail reports and candidate report APIs.
- v1.5.3: Added source-candidate lifecycle archiving.
- v1.5.2: Existing-task buttons jump to the matching task card inside 待办.
