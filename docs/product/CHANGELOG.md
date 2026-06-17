# Product Changelog

## v3.0.1 - 2026-06-17

### Product Decision
- V3.0.1 corrects the report page flow: the normal action is uploading a report file, and warning generation runs automatically after upload.
- The example-data trigger is now a backup demo path, not the primary product action.
- Long data version IDs are shortened in cards so the report page layout stays stable.

### Changed
- Report page hero now shows `上传报表` as the main card.
- Added report type selection for inventory, refunds, orders, products, and customers.
- Added browser-side CSV parsing, then posts rows to `/api/data/import/report`.
- Upload success refreshes V3 summary, module data, and task state.
- Backup demo action is renamed to `备用：使用示例数据试跑`.
- Frontend assets now use `?v=3.0.1`; API and health versions are aligned.

### Product Boundary
- Current file path supports CSV first.
- XLSX parsing and real ERP / CRM API sync should be later steps.
- Main product APIs remain `/api/modules/*`, `/api/accounts`, and `/api/data/*`.

## v3.0.0 - 2026-06-17

### Product Decision
- V3.0.0 adds report-driven data refresh and report-triggered warnings.
- Product truth: after importing a new report, the system state must change globally, not just add one report record.
- The new loop is: report import -> data version -> data snapshot -> rules -> alert event -> task pool -> dashboard / product / traffic / report / todo / log sync.
- Do not connect marketplace APIs too early; report import is the safe MVP path.

### Changed
- Added report-triggered warning runtime through `report_alert_service.py`.
- Added V3 data import and alert endpoints under `/api/data/*`.
- Report page added a demo action to import mock reports and generate alerts.
- Product and traffic cards expose `alertState` after report-triggered alerts are created.
- Dashboard payload includes V3 data refresh summary.
- Frontend assets now use `?v=3.0.0`; API and health versions are aligned.

### Product Boundary
- V3.0 uses explainable rules first, not Agent autonomous execution.
- Agent can later enrich reports and checklists, but cannot directly change price, inventory, ad budget, product publishing, or customer contact.
- Tasks still reuse the V2.5.1 lifecycle system; report warnings must not create a parallel todo system.

## v2.5.1 - 2026-06-16

### Product Decision
- V2.5.1 adds cross-account task lifecycle sync.
- Product truth: tasks are one main record with multiple account views and lifecycle events, not separate copies for each account.
- Operator accept, submit, manager return, manager approve, and recap actions must update related account task status, counters, logs, and recap entry.
- MVP first guarantees data consistency after refresh; polling, SSE, WebSocket, or notifications can come later.

### Changed
- Added lifecycle event stream: `TASK_EVENTS`.
- Added unified `transition_task()` path for task lifecycle actions.
- Added operator `接收任务` stage before processing.
- Operator submission now changes manager view to `待复核` and creates an `operator_submitted` event.
- Manager approval / return creates lifecycle events and updates operator view.
- Writing a task to recap creates a `task_written_to_recap` event and makes recap handoff visible to owner / manager scopes.
- Added per-user counters: waiting accept, processing, submitted, reviewing, returned, recap pending, and lifecycle events.
- Added `/todo/events`, `/todo/counters`, `/todo/{task_id}/accept`, `/todo/{task_id}/recap` endpoints.
- Todo page now shows a lifecycle event feed and cross-account counters.
- Frontend assets now use `?v=2.5.1`; API and health versions are aligned.

### Product Boundary
- This remains in-memory mock event sync.
- Real version should move events, counters, notifications, and lifecycle transitions into persistent tables and then connect polling / SSE / WebSocket.

## v2.5.0 - 2026-06-16

### Product Decision
- V2.5.0 rebuilds the task system from a single-account todo list into a role-permission-driven task flow.
- Product truth: tasks are business objects around store permissions, role responsibility, and recap handoff.
- Owner sees decision tasks, manager sees dispatch tasks, operator sees execution tasks.
- Product / competitor / listing / traffic warnings are routed by store ownership and account permissions.

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

- Optimized store-group manager processing order layout.

## v2.4.0 - 2026-06-16

- Changed owner dashboard from task list into business overview.

## Earlier History

- v2.3.9: Manager upgraded from a static execution board into an actionable task dispatch workbench.
- v2.3.8: Manager side changed into execution management workflow.
- v2.3.7: `账号` changed into a basic account center.
- v2.3.6: `复盘审计` changed from table-style rows into summary-first expandable cards.
- v2.3.5: Owner-side review audit changed into recap audit.
