# Changelog

## v1.1.2 - 2026-06-16

### Fixed
- Fixed the module-switch crash caused by `web_demo/module-task-bridge.js` repeatedly mutating button text inside a global `MutationObserver` loop.
- The task bridge observer is now throttled through `requestAnimationFrame`.
- Button text, class, and title updates are now idempotent, so repeated binding checks do not continuously rewrite DOM nodes.
- Frontend assets were bumped to `?v=1.1.2` to avoid cached bridge scripts.
- FastAPI app version and health version are aligned to `1.1.2`.

### Product Engineering Rule
- Module bridge scripts may observe route DOM changes, but they must not rewrite the same DOM nodes on every observer callback.
- Observer-based hotfix scripts should be throttled and idempotent, otherwise switching modules can create render loops.

## v1.1.1 - 2026-06-16

### Added
- Added task identity fields to the front-end task store: `entityType`, `entityId`, `riskDomain`, `actionType`, and `dedupeKey`.
- Added task-store helpers for dedupe matching: `buildDedupeKey()` and `findOpenTask()`.
- Added merge behavior for repeated same-problem tasks. If an active task already exists with the same dedupe key, the new action is merged into the existing task instead of creating a duplicate.
- Added source-trail and judgment-tag merging so repeated module actions still leave traceable context.

### Changed
- `web_demo/module-task-bridge.js` now checks task identity before creating a task.
- 商品、竞品、上新、流量 and 报表 buttons now show existing-task state when the same problem is already in 待办.
- Same-product same-problem manual actions now route to 待办 instead of creating another task.
- Different problem domains can still create separate tasks, such as `商品:P002:售后:复查` and `商品:P002:上新:测试`.
- Frontend assets were bumped to `?v=1.1.1`.
- FastAPI app version and health version are aligned to `1.1.1`.

### Product Engineering Rule
- Manual task creation is still allowed, but it must pass through task identity dedupe.
- Same entity + same risk domain + same action type means merge / view existing task.
- Same entity + different risk domain or action type can create a new task.
- This prevents the unified task pool from becoming noisy after modules begin generating tasks dynamically.

## v1.1.0 - 2026-06-16

### Added
- Added `web_demo/task-store.js` as the unified front-end task store for V1.1.
- Added `web_demo/module-task-bridge.js` so 商品、竞品、上新、流量 and 报表 actions can create shared tasks without direct high-risk execution.
- The task store now persists tasks and logs through browser `localStorage`, so refresh does not erase the current demo task flow.

### Changed
- Dashboard now reads top tasks from the unified task store instead of its own static dashboard-only pool.
- 待办 now reads the complete shared task pool and supports completion, pinning, up/down ordering, source jumps, and demo reset.
- 日志 now reads operation logs from the same task store, including task creation, completion, ordering, and module-triggered actions.
- `web_demo/index.html` now loads `task-store.js` before the business modules and loads `module-task-bridge.js` after all module scripts.
- Frontend asset cache version was bumped to `?v=1.1.0`.
- FastAPI app version and health version are aligned to `1.1.0`.

### Product Engineering Rule
- V1.1 is a dynamic task-flow release, not a UI copy patch.
- 商品、竞品、上新、流量、报表 should push tasks into the shared task pool.
- 首页 is the command board; 待办 is the full task pool; 日志 is the trace record.
- AI and module actions only create advice/tasks/logs in this version. They do not change real shop data, ad budgets, refunds, pricing, or ERP records.

## Earlier History

- v1.0.24: Dashboard task board was simplified into a command-board scheduling view with short judgment tags.
- v1.0.23: Dashboard task board linked the homepage to a cross-module task pool.
- v1.0.22: Report page became 日志 / operation log center.
- v1.0.21: Actions page became 待办任务 / task center.
- v1.0.20: Traffic page was repositioned as `流量测试台`.
- v1.0.19: Listing page was repositioned as `上新测试台`.
- v1.0.18: Productized the 竞品 page from an analysis result panel into a competitor observation list.
- v1.0.17: Product page was switched from forced table columns to responsive product cards.
- v1.0.16: Product list layout was hardened for long titles.
- v1.0.15: Productized the 商品 page from oversized diagnosis cards into a compact goods-operation list.
- v1.0.14: Report pages support real export and template download.
- v1.0.13: Report center added user-driven report import.
- v1.0.11: Data page was renamed and productized into `ERP / CRM 报表管理`.
- v1.0.10: Operating unit page was productized into a store-group management surface.
- v1.0.9: Added dashboard cache hotfix and compatibility CSS.
- v1.0.8: Compact dashboard task board was added.
- v1.0.7: Homepage overview was repositioned as a task board.
- v1.0.0-v1.0.6: Product trunk cleanup, API alignment, health/version repair, and current route governance.
