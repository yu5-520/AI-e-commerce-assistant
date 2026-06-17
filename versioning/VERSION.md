# Version

Current Version: v3.1.1

## Version History

- v3.1.1: Added report import-record management, data-version soft rollback, rollback audit records, report-page rollback cards, and rollback health flags.
- v3.1.0: Added standalone inventory and customer-service centers, store-scoped inventory / service task routes, manager operation-module entries, and operation-center UI pages.
- v3.0.9: Added automatic recap candidates after manager evidence approval, recap candidate service and endpoint, log-page recap candidate board, and automatic复盘候选 logs for daily / weekly review.
- v3.0.8: Added structured task evidence submission, manager evidence review, evidence records, review records, task evidence endpoints, and the Todo handling form so tasks are submitted with audit material instead of completed by a bare click.
- v3.0.7: Added alert evidence detail reports with source trace, trigger rule, store responsibility, raw report rows, evidence chain, and frontend entry from latest report alerts.
- v3.0.6: Hardened report data ownership by binding imported report rows, alert events, dashboard summary, report module alerts, and generated warning tasks to store scope; added store_id / store_name field aliases and account-scoped alert APIs.
- v3.0.5: Compacted manager navigation, nested product / competitor / listing / traffic / report operation pages under the manager operation-module hub, added clickable manager module cards, and extended minimal UI cleanup to manager pages.
- v3.0.4: Added minimal UI cleanup, removed explanatory grey microcopy through a global UI layer, changed store owner changes into confirmed next-day migration records, added pending store migrations, and changed owner-side store responsibility changes to require management confirmation.
- v3.0.3: Split operating-unit visibility from store responsibility permissions, added store assignments, scoped operating-unit/product/listing/traffic data by viewer store permissions, redesigned organization responsibility controls, and moved report upload into a separate layout panel.
- v3.0.2: Added report schema preview, field alias mapping, `/api/data/templates`, `/api/data/preview`, `/api/data/import/confirm`, frontend three-step import flow, preview table, and confirm-before-alert behavior.
- v3.0.1: Reworked the report page into a file-first upload flow, moved mock alert generation into a backup demo action, added client-side CSV parsing, improved report upload layout, and truncated long data versions in cards.
- v3.0.0: Added report-driven data snapshots, metric snapshots, alert events, alert-to-task bridge, V3 data summary API, one-click mock report alert import, and frontend alert sync for dashboard/report/product/traffic modules.
- v2.5.1: Added cross-account task lifecycle sync with task events, per-user counters, operator accept action, manager review sync, and recap handoff.
- v2.5.0: Rebuilt the task system into a role-scoped task flow with store permissions, visible roles/users/stores, owner decision tasks, manager dispatch tasks, operator execution tasks, warning-to-operator todo routing, and manager split endpoint.
- v2.4.2: Restored operator-side store operation modules and added a scoped operator dashboard for assigned stores, reports, products, competitors, listings, traffic, tasks, logs, and account settings.
- v2.4.1: Optimized the store-group manager task queue layout by restoring the schedule-style dispatch row with rank, time / priority, main task, source, judgment tags, and action buttons.
- v2.4.0: Rebuilt the owner `总览` from an execution task list into a business overview page with operating metrics, owner module entry cards, and decision attention items.
- v2.3.9: Added manager task sorting, task detail pages, split actions, dispatch actions, and Agent judgment placeholders for the store-group manager workflow.
- v2.3.8: Reworked the manager role into a store-group execution management workflow: 店群任务、任务派发、运营复核、经营模块、复盘提交、数据报表.
- v2.3.7: Simplified `账号` into a basic account center for profile, login security, phone / email / third-party binding, platform authorization status, notification settings, local cache, and logout actions.
- v2.3.6: Changed `复盘审计` from wide tables into expandable retrospective cards, audit detail cards, and next-cycle task draft cards with Agent judgment placeholders.

## Version Rules

- Patch: copy, prompt, template, or wording changes.
- Minor: new module, new mode, new interface, or new runtime config.
- Major: breaking workflow, API contract, schema, or folder migration changes.
