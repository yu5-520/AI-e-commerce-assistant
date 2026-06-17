# Product Changelog

## v3.0.5 - 2026-06-17

### Product Decision
- V3.0.5 cleans up the store-group manager workflow by nesting first-line operation modules inside `经营模块`.
- Product truth: the manager sidebar should show management actions, while product / competitor / listing / traffic / after-sales / inventory live inside the operation-module hub.
- Manager module cards should be actionable entry cards, not static dashboard cards.

### Changed
- Manager sidebar is compacted to: 总览、店群任务、任务派发、运营复核、经营模块、复盘提交、数据报表、经营单元、日志、账号。
- 商品、竞品、上新、流量、待办等 first-line entries are hidden from the manager sidebar.
- 经营模块 cards now navigate to detailed module pages.
- 售后 and 库存 currently route into the report page as their data source.
- Manager module cards were redesigned as clean clickable cards.
- Minimal UI cleanup now covers manager-page microcopy.
- Frontend assets now use `?v=3.0.5`; API and health versions are aligned.

### Product Boundary
- This is still a frontend route-layer compaction. Backend `visibleModules` can be tightened later, but the current bootstrap layer enforces the manager navigation scope.

## v3.0.4 - 2026-06-17

### Product Decision
- V3.0.4 moves the product toward a cleaner, higher-end interface by removing grey explanatory microcopy from UI modules.
- Store owner changes are treated as store-permission migrations, not instant toggles.
- Owner changes to store responsibility must be confirmed, recorded, and scheduled to take effect the next day because products, reports, warnings, open tasks, logs, and recaps may need to migrate.

### Changed
- Added a minimal UI layer that hides explanatory grey copy and keeps cards focused on title, number, state, and action.
- Added pending store migration records with old operator, new operator, effective date, reviewer, impact scope, and status.
- Organization page now uses a migration confirmation panel instead of direct owner-switch buttons.
- Store responsibility changes now remain pending until the next day; current operator data visibility does not change immediately.
- Pending migrations are displayed on affected store cards.
- API and health versions are aligned to `3.0.4`.

### Product Boundary
- This is still an in-memory MVP migration queue. Real production should persist migrations, require real account verification, send notifications to affected operators, and define how open tasks are migrated or retained.

## v3.0.3 - 2026-06-17

### Product Decision
- V3.0.3 splits operating-unit visibility from store responsibility permissions.
- Product truth: 总管能看到经营单元内全部店铺和商品数据；运营能进入共同经营单元，但只能看到自己负责店铺内的商品、报表、预警、待办和日志。
- Report upload UI should not be squeezed into the hero card; upload is a primary operation panel below the page headline.

### Changed
- Added store responsibility assignments: store -> operating unit -> primary operator -> reviewer.
- Added owner-side “店铺运营责任分配” panel in 组织效率.
- Added store-scoped payloads for 经营单元, 商品, 上新, and 流量 modules.
- Operator A now owns 家居生活主店 / 家居百货店; Operator B owns 家居好物号 / 家清收纳店.
- Report upload moved into a separate horizontal panel; the hero area now only explains the current import flow.
- Frontend assets now use `?v=3.0.3`; API and health versions are aligned.

### Product Boundary
- 经营单元 is shared business context; store responsibility is the operator data boundary.
- Store-scoped filtering now covers core operation modules, but report row-level filtering and persisted task tables still need later hardening.

## v3.0.2 - 2026-06-17

### Product Decision
- V3.0.2 adds report field precheck before warning generation.
- Product truth: upload does not mean import; users should see field recognition, missing fields, and preview rows before creating warnings or tasks.
- The normal flow is: choose report type -> upload CSV -> preview field mapping -> confirm import -> generate warnings -> sync tasks and modules.

### Changed
- Added schema templates and alias matching for inventory, refunds, orders, products, and customers.
- Added `/api/data/templates`, `/api/data/preview`, and `/api/data/import/confirm`.
- Report page now shows recognized fields, missing fields, import impact, and the first five rows before confirmation.
- Confirm import reuses the existing V3 alert-to-task bridge after mapped fields are normalized.
- Frontend assets now use `?v=3.0.2`; API and health versions are aligned.

### Product Boundary
- Current precheck supports CSV rows and common Chinese / English field aliases.
- XLSX parsing, manual field remapping UI, rollback, and real ERP / CRM API sync should be later steps.
- Main product APIs remain `/api/modules/*`, `/api/accounts`, and `/api/data/*`.

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
