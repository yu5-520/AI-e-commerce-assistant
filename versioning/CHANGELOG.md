# Changelog

## v3.0.1 - 2026-06-17

### Changed
- Reworked the report page from demo-trigger-first into file-upload-first.
- Changed the main report card action from `一键生成预警` to `上传报表`.
- Moved mock alert generation into a low-priority backup action: `备用：使用示例数据试跑`.
- Added client-side CSV parsing so a selected CSV report is converted into rows and sent to `/api/data/import/report`.
- Upload completion now automatically refreshes task state, module data, and V3 summary.
- Long data versions are truncated in metrics and alert cards to avoid layout overflow.
- Report upload card layout was rebuilt to reduce the visual weight of the backup demo action.
- Frontend assets were bumped to `?v=3.0.1`.
- FastAPI app version and health version are aligned to `3.0.1`.

### Product Engineering Rule
- Normal user action is `上传报表`; generating warnings is a system action after upload.
- The example-data trigger remains only as a demo / fallback path, not the primary product flow.

## v3.0.0 - 2026-06-17

### Added
- Added V3 report-driven data refresh runtime: report import → data snapshot → alert event → task bridge → global module sync.
- Added `src/services/report_alert_service.py` for V3 SQLite tables, data versions, metric snapshots, alert events, alert-to-task payloads, and dashboard summary.
- Added V3 data endpoints: `/api/data/import/report`, `/api/data/import/mock-alerts`, `/api/data/versions`, `/api/data/versions/latest`, `/api/data/alerts`, `/api/data/alerts/entity/{entity_type}/{entity_id}`, and `/api/data/v3-summary`.
- Added one-click frontend action in the report page to generate mock report alerts and refresh modules/tasks.
- Added alert state sync to product and traffic modules so report-triggered alerts are visible outside the report page.
- Added V3 documentation at `docs/V3.0_REPORT_ALERT_RUNTIME.md`.

### Changed
- FastAPI app version and health version are aligned to `3.0.0`.
- Dashboard payload now includes `v3` and `data_refresh` summary fields.
- Report module now returns V3 summary and recent active alerts.
- Frontend assets were bumped to `?v=3.0.0`.
- README and version rules now describe the V3 data-version and alert-event architecture.

### Product Engineering Rule
- V3.0 does not connect Taobao / Pinduoduo / Douyin APIs directly yet; the safe MVP path is report import first.
- Data changes must become traceable versions before they generate warnings.
- Warnings must become task events through the existing task lifecycle, not a parallel todo system.
- The system can create tasks and reports, but it must not automatically change price, inventory, ad budget, product publishing, or customer messages.

## v2.5.1 - 2026-06-16

### Added
- Added cross-account task lifecycle sync on top of the V2.5.0 role-scoped task flow.
- Added `TASK_EVENTS` in `src/services/module_task_service.py` as an in-memory task event stream.
- Added lifecycle events for task creation, split, assignment, operator acceptance, operator submission, manager return, manager approval, completion, recap handoff, pinning, and reorder.
- Added `transition_task()` so task actions update state, create an event, write a log, and return sync context in one path.
- Added per-user task counters for waiting accept, processing, submitted, reviewing, returned, recap pending, and recent events.
- Added endpoints: `/api/modules/todo/events`, `/api/modules/todo/counters`, `/api/modules/todo/{task_id}/accept`, and `/api/modules/todo/{task_id}/recap`.
- Added client fallback lifecycle event support in `web_demo/stores/task-store.js`.
- Added lifecycle event feed and cross-account counters in the Todo page.

### Changed
- Operator tasks now support an explicit `接收任务` stage before processing.
- Operator submission now creates an `operator_submitted` event and moves manager view to `待复核`.
- Manager approval / return now creates corresponding lifecycle events that update operator view.
- Writing a task to recap creates a lifecycle event and makes recap handoff visible to owner / manager scopes.
- Frontend assets were bumped to `?v=2.5.1`.
- FastAPI app version and health version are aligned to `2.5.1`.

### Product Engineering Rule
- 任务不是每个账号各自一份，而是一条主记录、多账号视图、多生命周期事件。
- 任何任务动作都要同步改变相关账号的任务状态、待办数量、日志记录和复盘入口。
- MVP 先用刷新后的数据一致性，后续再接轮询、SSE、WebSocket 或消息通知。

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

- Restored operator-side navigation to scoped store operation modules.

## v2.4.1 - 2026-06-16

- Optimized the store-group manager `今日处理顺序` and task-list layout.

## v2.4.0 - 2026-06-16

- Added owner-specific business overview dashboard and removed execution task list from owner `总览`.

## Earlier History

- v2.3.9: Added manager task sorting, task detail route, task actions, and mock state transitions.
- v2.3.8: Added manager-specific execution pages and store-group execution management flow.
- v2.3.7: `账号` was simplified into a basic account center.
- v2.3.6: `复盘审计` changed from wide tables into expandable retrospective cards.
- v2.3.5: Rebuilt owner-facing `复核审计` into `复盘审计`.
