# Changelog

## v2.3.9 - 2026-06-16

### Added
- Added manager task sorting by time, priority, source, and status.
- Added manager task detail route `manager-task-detail` with source report, impact scope, evidence, Agent judgment placeholders, and suggested split actions.
- Added task card actions: 查看详情、拆分任务、派发运营.
- Added mock state transitions for manager tasks: 待拆分 → 待派发 → 已派发 → 待复核 → 已归档.
- Added dashboard-side manager task actions so the manager overview can jump directly to task detail or dispatch/review pages.

### Changed
- Manager task lists now behave like an action workbench instead of a static board.
- Manager dispatch page now filters and sorts tasks needing split / dispatch.
- Frontend assets were bumped to `?v=2.3.9`.
- FastAPI app version and health version are aligned to `2.3.9`.

### Product Engineering Rule
- 店群总管不是只看任务，而是按时间、优先级、来源和状态处理任务。
- 每个任务必须能进入详情页，后续 Agent 的信息检索、证据判断、拆分建议和复核判断都应落在详情页。

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

- Added global mock account switching and role-based task visibility.

## v2.0.0 - 2026-06-16

- Added `/api/accounts` and upgraded the task pool into dispatch / submit / review collaboration flow.

## Earlier History

- v1.6.1: Candidate report pages include `加入任务清单` and jump to the matching 待办 task.
- v1.6.0: Added independent task detail reports and candidate report APIs.
- v1.5.3: Added source-candidate lifecycle archiving.
- v1.5.2: Existing-task buttons jump to the matching task card inside 待办.
