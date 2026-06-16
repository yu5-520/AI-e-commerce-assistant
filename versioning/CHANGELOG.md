# Changelog

## v2.5.0 - 2026-06-16

### Added
- Rebuilt `src/services/module_task_service.py` around a role-scoped task flow model.
- Added task fields for `taskLayer`, `sourceType`, `ownerRole`, `parentTaskId`, `childTaskIds`, `storeIds`, `storeGroupId`, `visibleRoleIds`, `visibleUserIds`, `visibleStoreIds`, `recapTarget`, and `agentJudgment`.
- Added warning-to-operator routing: product / competitor / listing / traffic warnings are assigned to the operator responsible for the affected store and remain visible to the store-group manager.
- Added manager split endpoint: `POST /api/modules/todo/{task_id}/split`.
- Added client-side fallback filtering in `web_demo/stores/task-store.js` so local mock tasks still respect role / user / store scope when the API falls back.

### Changed
- `/api/modules/todo` now returns task lists filtered by current account role, responsible store, assignee, reviewer, and visible role / user / store fields.
- Owner no longer receives ordinary operator execution tasks through the task pool.
- Manager receives group dispatch / review / warning tasks.
- Operator receives assigned tasks or warning tasks within their authorized store scope.
- Finance receives finance / report / ROI / inventory related tasks.
- Frontend assets were bumped to `?v=2.5.0`.
- FastAPI app version and health version are aligned to `2.5.0`.

### Product Engineering Rule
- 任务不是单个账号的待办列表，而是围绕店铺权限、角色职责和复盘链路流转的经营对象。
- 老板看决策任务，总管看调度任务，运营看执行任务。
- 模块预警不是进入全局待办，而是根据店铺归属和账号权限生成可见任务。

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

- Added owner-specific business overview dashboard and removed execution task list from owner `总览`.

## v2.3.9 - 2026-06-16

- Added manager task sorting, task detail route, task actions, and mock state transitions.

## v2.3.8 - 2026-06-16

- Added manager-specific execution pages and store-group execution management flow.

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
