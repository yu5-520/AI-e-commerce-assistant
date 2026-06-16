# Version

Current Version: v2.0.0

## Version History

- v0.1.0-v0.9.2: Early workflow, RAG, frontend, generation, and Agent governance iterations.
- v1.0.0-v1.0.6: Product trunk cleanup, script repair, legacy route removal, active API alignment, and server startup fixes.
- v1.0.7-v1.0.14: Dashboard task board, operating unit, ERP/CRM report center, import/export, and frontend cache/version governance were added.
- v1.0.15-v1.0.20: 商品、竞品、上新 and 流量 pages were productized into compact operating surfaces.
- v1.0.21: Actions page was repositioned as `待办任务`, showing tasks from 商品、竞品、上新、流量、报表 and AI 自动判定.
- v1.0.22: Report page was repositioned as `日志`, recording task completion, AI judgment, data import/export, and user actions.
- v1.0.23: Dashboard task board used a unified cross-module task pool for homepage summaries.
- v1.0.24: Dashboard task board was simplified into a command-board scheduling view with short judgment tags.
- v1.1.0: Added a unified front-end task store and dynamic module-driven task flow.
- v1.1.1: Added task identity and dedupe keys for same-product same-problem task merging.
- v1.1.2: Fixed the module task bridge render loop and repeated DOM mutation loops when switching modules.
- v1.2.0: Added a unified front-end route lifecycle coordinator.
- v1.3.0: Rebuilt the frontend into a modular route registry and removed legacy hotfix scripts from the active product entry.
- v1.4.0: Added modular backend interfaces under `/api/modules/*`, added the frontend `core/api-client.js`, prefetches module data before router start, and removed the old `/api/business/*` router from the active backend entry.
- v1.4.1: Closed the module API chain. Backend mock data moved into `module_data_service`, task/log authority moved into `module_task_service`, frontend full mock data was reduced to minimal fallback, task actions now call backend module endpoints, and todo/log pages now hydrate from server task state.
- v1.5.0: Split the backend module router into separate route files for dashboard, operating unit, product, competitor, listing, traffic, report, todo, and log. `src/api/routes/modules/__init__.py` now only aggregates routers under `/api/modules/*`.
- v1.5.1: Removed remaining task-identity duplication. Product task identity and active-task status now come from the backend; the frontend task store no longer infers risk/action domains. Dashboard now routes through `dashboard_service`, and the API badge exposes fallback failure details.
- v1.5.2: Unified existing-task button behavior across product, competitor, listing, traffic, and report modules. Existing task buttons now jump to the matching task card in 待办, and backend task-state annotations were added for competitor, listing, and report modules.
- v1.5.3: Added source-candidate lifecycle archiving. Completed tasks now archive their source candidate, source modules hide completed candidates by default, and the frontend refreshes module data after task lifecycle changes so completed work frees the next cycle slot.
- v1.6.0: Added independent task detail report pages. 待办 tasks now have `详情报告`; source modules have `查看预警` / `任务报告`; backend exposes task and candidate report APIs as the future Agent report generation boundary.
- v1.6.1: Added report-to-task conversion. Candidate report pages now include `加入任务清单`, create the matching module task from the detail page, refresh task/module state, and jump to the new task in 待办.
- v2.0.0: Cleaned the architecture around the modular `/api/modules/*` trunk, added the `/api/accounts` role-permission layer, added the 账号 page, and upgraded the task pool into a dispatch / submit / review collaboration flow.

## Version Rules

- Patch: copy, prompt, template, or wording changes.
- Minor: new module, new mode, new interface, or new runtime config.
- Major: breaking workflow, API contract, schema, or folder migration changes.

## Logging Rule

- Any architecture-level cleanup, route removal, folder migration, or deployment-entry change must update both `versioning/CHANGELOG.md` and this file.
- Product-specific decisions should also update the matching log under `docs/product/`.
