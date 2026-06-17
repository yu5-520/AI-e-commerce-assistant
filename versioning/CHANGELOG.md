# Changelog

## v3.1.0 - 2026-06-17

### Added
- Added standalone inventory center API: `/api/modules/inventory` and `/api/modules/inventory/{product_id}/tasks`.
- Added standalone customer-service center API: `/api/modules/aftersales` and `/api/modules/aftersales/{product_id}/tasks`.
- Added `web_demo/modules/operation-centers-v310.js` for inventory and service center pages.
- Added `web_demo/operation-centers.css` for independent operation-center cards and rules.
- Added manager operation-module card routing to `inventory-center` and `service-center`.

### Changed
- Inventory and service are no longer temporary report-page entries from the manager module hub.
- Inventory tasks now use `riskDomain=库存`, source route `inventory-center`, and inherit store scope.
- Service tasks now use `riskDomain=售后`, source route `service-center`, and inherit store scope.
- Frontend assets were bumped to `?v=3.1.0`.
- FastAPI app version and health version are aligned to `3.1.0`.

### Product Engineering Rule
- Inventory and service are first-class operation centers, not report-file placeholders. Report imports can trigger their alerts, but day-to-day handling should happen in their own module pages.

## v3.0.9 - 2026-06-17

### Added
- Added `src/services/task_recap_service.py` for daily / weekly retrospective candidates.
- Added `/api/modules/recap-candidates` to expose recap candidate summary and candidate list.
- Added automatic recap candidate creation after manager evidence approval.
- Added recap candidate loading in `web_demo/core/api-client.js`.
- Added recap candidate board on the log page.

### Changed
- Approved task evidence now creates a `复盘候选` log record.
- Log page now separates recap candidates from raw task logs.
- Recap candidates include problem source, trigger data, handling action, handling result, evidence summary, review comment, operator, reviewer, store scope, and next suggestion.
- Frontend assets were bumped to `?v=3.0.9`.
- FastAPI app version and health version are aligned to `3.0.9`.

### Product Engineering Rule
- Task completion should automatically become management memory. Once evidence is reviewed and approved, the system should produce a recap candidate instead of relying on manual copying into daily / weekly reports.

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
