# Product Changelog

## v3.0.9 - 2026-06-17

### Product Decision
- V3.0.9 turns reviewed task handling evidence into management memory.
- Product truth: 任务完成不是终点；证据复核通过后，系统应自动沉淀为日报 / 周报复盘候选。
- This pushes the system from task execution into management review and cycle learning.

### Changed
- Added recap candidate runtime under `/api/modules/recap-candidates`.
- Manager evidence approval now automatically creates a recap candidate.
- Approved evidence also writes a `复盘候选` log record.
- Log page now shows a recap candidate board above raw task logs.
- Recap candidates show problem source, trigger data, handling action, handling result, evidence summary, review comment, responsible operator, reviewer, store scope, and next suggestion.
- Frontend assets now use `?v=3.0.9`; API and health versions are aligned.

### Product Boundary
- This is still an in-memory MVP recap queue. Production should persist daily / weekly / monthly recap drafts, support manager editing, owner approval, immutable audit logs, and export / notification workflows.

## v3.0.8 - 2026-06-17

### Product Decision
- V3.0.8 turns tasks from status buttons into evidence-based handling records.
- Product truth: 运营不能只是点完成；运营提交处理证据，总管复核证据，通过后任务才归档。
- This makes the task loop auditable before writing logs, retrospectives, and later Agent reports.

### Changed
- Added structured task evidence submission under `/api/modules/todo/{task_id}/submit-evidence`.
- Added manager evidence review under `/api/modules/todo/{task_id}/review-evidence`.
- Todo page now shows handling forms for库存、售后、流量、价格、报表任务.
- Evidence records include action, result, summary, domain fields, evidence links, follow-up flag, and recap flag.
- Manager review records include decision, comment, reviewer, and reviewed time.
- Evidence submission and review now write task logs and lifecycle transitions.
- Added task evidence UI styling.
- Frontend assets now use `?v=3.0.8`; API and health versions are aligned.

### Product Boundary
- This is still an in-memory MVP evidence workflow. Production should persist evidence files, add file upload / OSS storage, audit masking, role-based attachment access, and immutable review records.

## v3.0.7 - 2026-06-17

### Product Decision
- V3.0.7 turns report warnings into explainable evidence reports.
- Product truth: every warning must explain why it triggered, which report version and rows support it, which store owns it, who should handle it, and what remains a human decision.
- This makes the report-warning loop more trustworthy before adding more automation or real platform APIs.

### Changed
- Added alert evidence reports under `/api/modules/task-reports/alerts/{alert_id}`.
- Report page latest warnings now include a `证据报告` action.
- Detail report page now supports alert reports, not just task reports and candidate reports.
- Alert reports show source trace, trigger rule, responsibility, raw matching report rows, evidence chain, suggested actions, and human confirmation points.
- Added alert-report UI styling.
- Frontend assets now use `?v=3.0.7`; API and health versions are aligned.

### Product Boundary
- Raw report-row matching currently uses the imported snapshot sample rows and entity ID / store ID matching.
- Production should persist full normalized row evidence and support row-level audit, masking, and rollback.

## v3.0.6 - 2026-06-17

### Product Decision
- V3.0.6 hardens the core report loop by binding report rows, alerts, tasks, dashboard counts, and report-page warnings to store ownership.
- Product truth: 报表导入不是全局裸数据；每条报表数据都应尽量绑定店铺，预警和任务再继承店铺责任权限。
- 总管看经营单元内全量报表预警；运营只看自己负责店铺切片内的报表预警和任务。

### Changed
- Report schema preview now recognizes `store_id` and `store_name` aliases.
- Report alerts now carry `storeId`, `storeName`, and `visibleStoreIds`.
- Report-triggered warning tasks now inherit store scope and route toward the responsible store operator when applicable.
- `/api/data/alerts`, `/api/data/alerts/entity/*`, `/api/data/v3-summary`, `/api/modules/report`, and `/api/modules/dashboard` now scope report alert summaries by current account.
- Frontend assets now use `?v=3.0.6`; API and health versions are aligned.

### Product Boundary
- Store scope now resolves from report fields first, then falls back to product ownership in mock product data.
- Real production should require store identifiers from ERP / CRM imports and persist store-scoped snapshots for audit and rollback.

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
