# Changelog

## v3.0.8 - 2026-06-17

### Added
- Added `src/services/task_evidence_service.py` for structured task evidence submission and manager evidence review.
- Added `/api/modules/todo/{task_id}/evidence`, `/api/modules/todo/{task_id}/submit-evidence`, and `/api/modules/todo/{task_id}/review-evidence`.
- Added `web_demo/task-evidence.css` for task handling forms and manager review panels.
- Added task evidence client actions in `web_demo/core/api-client.js`.

### Changed
- Todo page now shows domain-specific handling forms for库存、售后、流量、价格、报表任务.
- Operators submit handling action, result, summary, domain fields, evidence links, follow-up flag, and recap flag before review.
- Managers review submitted evidence and can approve or return with comments.
- Evidence submission and review now write task records and logs before lifecycle transition.
- Frontend assets were bumped to `?v=3.0.8`.
- FastAPI app version and health version are aligned to `3.0.8`.

### Product Engineering Rule
- Tasks should not be completed by a bare click. Operators submit evidence, managers review evidence, and the evidence record becomes audit material for logs and retrospectives.

## v3.0.7 - 2026-06-17

### Added
- Added `src/services/alert_detail_service.py` for report-triggered alert evidence reports.
- Added `/api/modules/task-reports/alerts/{alert_id}` to return a scoped alert detail report.
- Added `web_demo/alert-report.css` for source trace, trigger rule, responsibility, raw report rows, and evidence-chain blocks.
- Added frontend alert-report navigation from the report page's latest warning cards.

### Changed
- The task report page now supports `alertId` route state in addition to task and candidate reports.
- Alert reports now show source dataset, data version, import batch, snapshot ID, trigger rule, responsible store, operator, reviewer, raw matching report rows, and processing checklist.
- Report page warning cards now expose a `证据报告` action even when the linked task is already created.
- Frontend assets were bumped to `?v=3.0.7`.
- FastAPI app version and health version are aligned to `3.0.7`.

### Product Engineering Rule
- Every warning must be explainable before it becomes trusted: why it triggered, which report version produced it, which rows support it, which store owns it, who should handle it, and what human decision remains.

## v3.0.6 - 2026-06-17

### Added
- Added store-scoped report alert ownership in `src/services/report_alert_service.py`.
- Added `store_id` support to persisted alert events and created an index for store-scoped alert lookup.
- Added `store_id` / `store_name` aliases to report schema preview.
- Added account-scoped `/api/data/alerts`, `/api/data/alerts/entity/*`, and `/api/data/v3-summary` responses.
- Added account-scoped report module V3 summaries and recent alerts.
- Added account-scoped dashboard data-refresh summary.

### Changed
- Report alerts now carry `storeId`, `storeName`, and `visibleStoreIds` when the row provides store fields or the product can resolve to a store.
- Report-triggered tasks now inherit `storeIds` / `visibleStoreIds`, so operator tasks can route to the store's responsible operator instead of becoming unscoped global warnings.
- Dashboard and report page alert counts now follow the current account's store visibility.
- Frontend assets were bumped to `?v=3.0.6`.
- FastAPI app version and health version are aligned to `3.0.6`.

### Product Engineering Rule
- Every imported business row should resolve to a store whenever possible.
- Report alerts, tasks, dashboard metrics, and report-page warnings must follow the same rule: manager sees the operating-unit store set; operators see only their assigned store slice.

## v3.0.5 - 2026-06-17

### Added
- Added `web_demo/modules/manager/manager-modules-v305.js` as a manager operation-module hub override.
- Added `web_demo/manager-module-hub.css` for clickable module cards.
- Added a manager-only navigation allowlist in `web_demo/bootstrap.js`.

### Changed
- Manager sidebar is now compacted to the management workflow: dashboard, group tasks, dispatch, review, operation modules, retrospectives, data reports, operating unit, logs, and account.
- Product, competitor, listing, traffic, todo, and report operation pages are no longer shown as separate manager sidebar entries.
- Manager operation-module cards now click through to the corresponding detailed module pages.
- Sales-after and inventory cards currently enter the report page as their data source.
- Minimal UI cleanup now also hides manager-page explanatory microcopy.
- Frontend assets were bumped to `?v=3.0.5`.
- FastAPI app version and health version are aligned to `3.0.5`.

### Product Engineering Rule
- Manager sidebar should represent management workflow, not every business module.
- Business modules live inside the operation-module hub and are opened from there when the manager needs to inspect causes or dispatch work.

## v3.0.4 - 2026-06-17

### Added
- Added `web_demo/minimal-ui.css` to remove explanatory grey microcopy and keep product screens cleaner.
- Added pending store migration records in `account_service`.
- Added `/api/accounts/store-migrations` for pending store-owner migrations.
- Added owner-side migration confirmation UI through `web_demo/modules/executive/org-responsibility-v304.js`.
- Added delayed store responsibility change behavior: store owner changes are recorded as pending migrations and take effect on the next day.

### Changed
- Organization page no longer applies store owner changes immediately.
- Store owner changes now require a management confirmation value and create a migration record with effective date, old operator, new operator, reviewer, and impact scope.
- Pending migration is displayed on the affected store while current store visibility remains unchanged until effective date.
- Bootstrap dynamically loads the minimal UI cleanup layer and the V3.0.4 organization responsibility override.
- FastAPI app version and health version are aligned to `3.0.4`.

### Product Engineering Rule
- UI should not explain every module with grey microcopy; cards should keep titles, numbers, state, and actions.
- Store ownership change is a data migration, not a simple toggle. It affects products, reports, warnings, open tasks, logs, and recaps, so it should be confirmed and delayed.

## v3.0.3 - 2026-06-17

### Added
- Added store responsibility assignments in `account_service`: each store now has an operating unit, primary operator, assistants, and reviewer.
- Added `/api/accounts/store-assignments/{store_id}` so owner accounts can assign which operator is responsible for each store.
- Added viewer-scoped operating-unit payloads: owner / manager see the full operating unit; operators see only their store slice.
- Added store permission filtering for product, listing, and traffic modules.
- Added `web_demo/report-layout-fix.css` to separate report upload from the hero area and fix the cramped report page layout.

### Changed
- Operating unit page now explains the rule: 经营单元共同可见，店铺权限决定商品、报表、预警和待办范围。
- Organization page now uses a “店铺运营责任分配” panel instead of mixing all possible stores into every user card.
- Operator A is responsible for 家居生活主店 / 家居百货店; Operator B is responsible for 家居好物号 / 家清收纳店.
- Report page upload now appears as a separate horizontal operation panel below the hero.
- Frontend assets were bumped to `?v=3.0.3`.
- FastAPI app version and health version are aligned to `3.0.3`.

### Product Engineering Rule
- 经营单元 is the shared business space; 店铺责任 is the operator data boundary.
- Manager sees all stores and product data within the operating unit; operator sees only stores, products, alerts, tasks, and logs within their assigned store scope.

## v3.0.2 - 2026-06-17

### Added
- Added report schema preview service: `src/services/report_schema_service.py`.
- Added field alias mapping for product, inventory, refund, order, customer, price, cost, and stock fields.
- Added endpoints: `/api/data/templates`, `/api/data/preview`, and `/api/data/import/confirm`.
- Added a confirm-before-alert import flow to the report page.
- Added preview table styling through `web_demo/report-preview.css`.

### Changed
- Report upload is now a three-step flow: upload file, preview fields, confirm import.
- CSV rows are previewed before alert generation; missing fields show product-facing guidance instead of silently failing.
- Confirm import normalizes mapped fields before reusing the existing alert and task bridge.
- Frontend assets were bumped to `?v=3.0.2`.
- FastAPI app version and health version are aligned to `3.0.2`.

### Product Engineering Rule
- Normal upload should never directly create tasks before the system has shown field recognition and preview rows.
- Active entries remain `/api/modules/*`, `/api/accounts`, and `/api/data/*`; V3.0.2 adds report trust checks before warnings.

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
- Active entries remain `/api/modules/*`, `/api/accounts`, and `/api/data/*`; V3.0.1 changes report-page workflow, not route ownership.

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
