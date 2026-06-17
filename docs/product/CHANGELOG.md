# Product Changelog

## v3.0.0 - 2026-06-17

### Product Decision
- V3.0.0 adds “准实时数据更新 + 报表触发预警”。
- Product truth: 上传 / 导入新报表后，系统状态必须全局变化，而不是只新增一条报表记录。
- 新链路为：报表导入 → 数据版本 → 数据快照 → 异常规则 → 预警事件 → 任务池 → 首页 / 商品 / 流量 / 报表 / 待办 / 日志同步。
- 先不接淘宝、拼多多、抖音平台 API，避免平台权限、风控、接口稳定性和合规复杂度过早拖垮 MVP。

### Changed
- Added report-triggered warning runtime through `report_alert_service.py`.
- Added V3 data import and alert endpoints under `/api/data/*`.
- Report page now has a one-click action to import mock reports and generate alerts.
- Product and traffic cards now expose `alertState` after report-triggered alerts are created.
- Dashboard payload now includes V3 data refresh summary.
- Frontend assets now use `?v=3.0.0`; API and health versions are aligned.

### Product Boundary
- V3.0 uses explainable rules first, not Agent autonomous execution.
- Agent can later enrich reports and checklists, but cannot directly change price, inventory, ad budget, product publishing, or customer messages.
- Tasks still reuse the V2.5.1 lifecycle system; report warnings must not create a parallel todo system.

## v2.5.1 - 2026-06-16

### Product Decision
- V2.5.1 adds cross-account task lifecycle sync.
- Product truth: 任务不是每个账号各自一份，而是一条主记录、多账号视图、多生命周期事件。
- 运营接收、提交、总管退回、总管通过、写入复盘等动作，必须同步改变相关账号的任务状态、待办数量、日志记录和复盘入口。
- MVP 先保证刷新后的数据一致性；后续再接轮询、SSE、WebSocket 或消息通知。

### Changed
- Added lifecycle event stream: `TASK_EVENTS`.
- Added unified `transition_task()` path for task lifecycle actions.
- Added operator `接收任务` stage before processing.
- Operator submission now changes manager view to `待复核` and creates an `operator_submitted` event.
- Manager approval / return creates lifecycle events and updates operator view.
- Writing a task to recap creates a `task_written_to_recap` event and makes recap handoff visible to owner / manager scopes.
- Added per-user counters: 待接收、处理中、已提交、待复核、已退回、待写复盘、生命周期事件.
- Added `/todo/events`, `/todo/counters`, `/todo/{task_id}/accept`, `/todo/{task_id}/recap` endpoints.
- Todo page now shows a lifecycle event feed and cross-account counters.
- Frontend assets now use `?v=2.5.1`; API and health versions are aligned.

### Product Boundary
- This remains in-memory mock event sync.
- Real version should move events, counters, notifications, and lifecycle transitions into persistent tables and then connect polling / SSE / WebSocket.

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

- Restored operator-side operation modules and scoped operator store dashboard.

## v2.4.1 - 2026-06-16

- Optimized 店群总管 `今日处理顺序` into schedule-row dispatch queue layout.

## v2.4.0 - 2026-06-16

- Changed 老板账号 `总览` from task list into business overview.

## Earlier History

- v2.3.9: 店群总管 upgraded from a static execution board into an actionable task dispatch workbench.
- v2.3.8: 店群总管 side changed into execution management workflow.
- v2.3.7: `账号` changed into a basic account center.
- v2.3.6: `复盘审计` changed from table-style rows into summary-first expandable cards.
- v2.3.5: Owner-side `复核审计` changed into `复盘审计`.
- v2.3.4: Owner-side `组织效率` changed into organization governance console.
- v2.3.3: Owner-side `利润预算` changed into `供投财务`.
- v2.3.2: Owner-side `任务指挥` changed into `人员总览`.
- v2.3.1: `店群总览` was upgraded into a realtime business operations board.
- v2.3.0: Removed owner `经营驾驶舱` and repositioned `风险中心` into `店群总览`.
