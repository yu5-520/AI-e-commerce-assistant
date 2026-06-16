# Version

Current Version: v2.5.0

## Version History

- v2.5.0: Rebuilt the task system into a role-scoped task flow with store permissions, visible roles/users/stores, owner decision tasks, manager dispatch tasks, operator execution tasks, warning-to-operator todo routing, and manager split endpoint.
- v2.4.2: Restored operator-side store operation modules and added a scoped operator dashboard for assigned stores, reports, products, competitors, listings, traffic, tasks, logs, and account settings.
- v2.4.1: Optimized the store-group manager task queue layout by restoring the schedule-style dispatch row with rank, time / priority, main task, source, judgment tags, and action buttons.
- v2.4.0: Rebuilt the owner `总览` from an execution task list into a business overview page with operating metrics, owner module entry cards, and decision attention items.
- v2.3.9: Added manager task sorting, task detail pages, split actions, dispatch actions, and Agent judgment placeholders for the store-group manager workflow.
- v2.3.8: Reworked the manager role into a store-group execution management workflow: 店群任务、任务派发、运营复核、经营模块、复盘提交、数据报表.
- v2.3.7: Simplified `账号` into a basic account center for profile, login security, phone / email / third-party binding, platform authorization status, notification settings, local cache, and logout actions.
- v2.3.6: Changed `复盘审计` from wide tables into expandable retrospective cards, audit detail cards, and next-cycle task draft cards with Agent judgment placeholders.
- v2.3.5: Rebuilt owner `复核审计` into `复盘审计`, receiving daily / weekly / monthly retrospectives, auditing missed targets and forming next-cycle task drafts.
- v2.3.4: Rebuilt owner `组织效率` into an organization governance console with position relationship network, account role control, store authorization, and permission template control.
- v2.3.3: Rebuilt owner `利润预算` into `供投财务`, combining supply, traffic, and finance views.
- v2.3.2: Owner-side task command was repositioned into `人员总览`.
- v2.3.1: Fixed `店群总览` layout and upgraded it into a realtime operations board.
- v2.3.0: Removed redundant owner `经营驾驶舱`; changed `风险中心` into `店群总览`.
- v2.2.0: Refactored owner navigation from first-line operation modules into executive modules and added the role permission console.
- v2.1.0: Added global mock account switching, role-based task visibility, permission-based todo actions, and role-specific insight depth.
- v2.0.0: Added `/api/accounts`, account roles, permissions, and the dispatch / submit / review collaboration flow.
- v1.0.0-v1.6.1: Product trunk cleanup, modular backend/frontend, task lifecycle, detail reports, and report-to-task conversion.
- v0.1.0-v0.9.2: Early workflow, RAG, frontend, generation, and Agent governance iterations.

## Version Rules

- Patch: copy, prompt, template, or wording changes.
- Minor: new module, new mode, new interface, or new runtime config.
- Major: breaking workflow, API contract, schema, or folder migration changes.

## Logging Rule

- Any architecture-level cleanup, route removal, folder migration, or deployment-entry change must update both `versioning/CHANGELOG.md` and this file.
- Product-specific decisions should also update the matching log under `docs/product/`.
