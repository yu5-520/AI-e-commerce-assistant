# Version

Current Version: v1.1.2

## Version History

- v0.1.0-v0.9.2: Early workflow, RAG, frontend, generation, and Agent governance iterations.
- v1.0.0-v1.0.6: Product trunk cleanup, script repair, legacy route removal, active API alignment, and server startup fixes.
- v1.0.7-v1.0.14: Dashboard task board, operating unit, ERP/CRM report center, import/export, and frontend cache/version governance were added.
- v1.0.15-v1.0.20: 商品、竞品、上新 and 流量 pages were productized into compact operating surfaces.
- v1.0.21: Actions page was repositioned as `待办任务`, showing tasks from 商品、竞品、上新、流量、报表 and AI 自动判定.
- v1.0.22: Report page was repositioned as `日志`, recording task completion, AI judgment, data import/export, and user actions.
- v1.0.23: Dashboard task board used a unified cross-module task pool for homepage summaries.
- v1.0.24: Dashboard task board was simplified into a command-board scheduling view with short judgment tags.
- v1.1.0: Added a unified front-end task store and dynamic module-driven task flow. 商品、竞品、上新、流量 and 报表 can now create shared tasks; dashboard and 待办 read the same task pool; task actions create operation logs; refresh preserves the demo task state through localStorage.
- v1.1.1: Added task identity and dedupe keys. Manual module actions now check `entityType + entityId + riskDomain + actionType`; same-product same-problem tasks are merged or routed to existing 待办 instead of duplicated, while different problem domains can still create separate tasks.
- v1.1.2: Fixed the module task bridge render loop. The bridge observer is now throttled with `requestAnimationFrame`, button state updates are idempotent, and repeated text updates no longer trigger continuous DOM mutation loops when switching modules.

## Version Rules

- Patch: copy, prompt, template, or wording changes.
- Minor: new module, new mode, new interface, or new runtime config.
- Major: breaking workflow, API contract, schema, or folder migration changes.

## Logging Rule

- Any architecture-level cleanup, route removal, folder migration, or deployment-entry change must update both `versioning/CHANGELOG.md` and this file.
- Product-specific decisions should also update the matching log under `docs/product/`.
