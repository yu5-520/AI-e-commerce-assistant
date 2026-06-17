# Product Changelog

## v3.1.4 - 2026-06-17

### Product Decision
- V3.1.4 stops adding new features and repairs the current frontend / backend breakpoints.
- Product truth: once a feature starts depending on multiple frontend list calls, versioned file names, and duplicate loaders, the product becomes harder to operate and debug.
- Data-version detail should be a backend business payload. Frontend should display it, not reassemble it from unrelated lists.

### Changed
- Added backend data-version detail payload under `/api/data/versions/{data_version}/detail`.
- Report detail page now reads one detail payload containing the record, alerts, linked tasks, rollback, summary, and permissions.
- Data-version service version is aligned to `3.1.4`.
- Replaced `report-v311.js` with `report-runtime.js` and `manager-modules-v305.js` with `manager-modules.js`.
- Removed duplicate bootstrap dynamic loading; `index.html` is now the page module loading authority.
- Deleted unused old report and manager versioned runtime files.
- Frontend assets now use `?v=3.1.4`; API and health versions are aligned.

### Product Boundary
- Operation center and organization override files still carry old filename suffixes because they need a separate safe rename pass. They remain referenced and functional, but are now isolated as the remaining cleanup items.

## v3.1.3 - 2026-06-17

### Product Decision
- V3.1.3 cleans the report page hierarchy so operators see the report workflow first and data-version management last.
- Product truth: 导入记录是审计与回滚工具，不是报表页主流程。首页只展示摘要，详情页承载完整版本信息和回滚策略。
- Operator accounts can view version records and details, but rollback remains a management-level action.

### Changed
- Import records are moved to the bottom of the report page.
- Import records are compacted into list rows instead of large cards.
- Added a data-version detail route for full version information, alert impact, linked tasks, rollback records, and rollback controls.
- Rollback task strategy moved from the record list into the detail page.
- Rollback buttons are hidden from operator accounts and backend rollback is restricted to owner / manager / finance roles.
- Frontend assets now use `?v=3.1.3`; API and health versions are aligned.

### Product Boundary
- Current detail page uses existing snapshot, alert, and rollback data. Production should add immutable audit pages, permission logs, and owner approval for high-impact rollback.

## v3.1.2 - 2026-06-17

### Product Decision
- V3.1.2 completes the rollback product loop by defining what happens to tasks created by a wrong report version.
- Product truth: 预警可以回滚，但已经生成的待办不能假装不存在。它们必须被转人工复核、归档保留审计，或明确保持当前状态。
- This prevents silent task loss while keeping the system operable after wrong report uploads.

### Changed
- Data-version rollback now accepts a linked-task strategy.
- Default strategy is `review`: active linked tasks become `待复核` with `数据回滚待复核` workflow status.
- `archive` keeps audit history and removes linked active tasks from the active queue.
- `keep` records rollback impact but preserves current task status.
- Report page import records now include a linked-task strategy selector before rollback.
- Rollback result now reports affected alerts and affected tasks.
- Frontend dynamic assets now use `?v=3.1.2`; API and health versions are aligned.

### Product Boundary
- Current strategy is MVP-level task-state handling. Production should require manager / owner confirmation for high-impact rollback, task cancellation records, and immutable audit trails.

## v3.1.1 - 2026-06-17

### Product Decision
- V3.1.1 solves the operational problem of uploading the wrong report.
- Product truth: 上传报表是数据版本动作，不是不可逆动作。错误版本应该可以回滚，但必须留下审计记录。
- This makes the report runtime safer before connecting real ERP / CRM adapters.

### Changed
- Added import-record management under `/api/data/import-records`.
- Added data-version rollback under `/api/data/versions/{data_version}/rollback`.
- Report page now shows import records, active alerts, generated tasks, rollback state, and rollback history.
- Rolling back a version soft-removes that version's active alerts from dashboards and report warning lists.
- Linked tasks and historical evidence are kept for audit instead of being deleted.
- Added rollback UI styling and dynamic bootstrap loading.
- Frontend assets can be refreshed with `?v=3.1.1`; API and health versions are aligned.

### Product Boundary
- Current rollback is soft rollback for alert events. Production should also support task cancellation rules, attachment retention, owner approval for rollback, and irreversible audit logs.

## v3.1.0 - 2026-06-17

### Product Decision
- V3.1.0 makes inventory and customer-service handling independent operation centers.
- Product truth: 库存和售后不能长期藏在报表页里；报表负责触发预警，经营中心负责日常处理和任务归属。
- This gives the manager operation-module hub a complete six-module structure: 商品、竞品、上新、流量、库存、售后。

### Changed
- Added standalone inventory center API and page.
- Added standalone customer-service center API and page.
- Manager `经营模块` cards now open库存中心 and售后中心 instead of routing both into报表.
- Inventory center shows SKU count, danger / warning / normal inventory states, handling rules, and store-scoped task creation.
- Customer-service center shows abnormal / sensitive / normal service states, service归因 rules, and store-scoped task creation.
- Frontend assets now use `?v=3.1.0`; API and health versions are aligned.

### Product Boundary
- Current V3.1.0 data still derives from mock product and report-alert data. Production should connect inventory and service centers to ERP / CRM adapters, full row-level evidence, and persistent task records.
