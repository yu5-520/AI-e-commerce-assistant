# Product Changelog

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
