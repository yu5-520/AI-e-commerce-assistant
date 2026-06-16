# Product Changelog

## v1.3.0 - 2026-06-16

### Product Decision
- V1.3.0 turns the frontend from hotfix-script stacking into a modular route-registry structure.
- The product goal is that future changes touch one module at a time instead of disturbing other pages.
- Product truth: shared state lives in stores, shared routing/shell logic lives in core, and business pages live under modules.

### Changed
- Added `web_demo/core/` for shell, router, task actions, and mock data registry.
- Added `web_demo/stores/task-store.js` as the current task-state source.
- Added `web_demo/modules/*/page.js` for dashboard, operating unit, report, product, competitor, listing, traffic, todo, and log.
- Added `web_demo/bootstrap.js` as the single module registration entry.
- `index.html` now loads the modular entry chain only and uses `?v=1.3.0`.
- Task generation is no longer done by a global task bridge scanning the DOM; each module binds its own task actions through the router context.

### Removed
- Removed the old root task store, legacy app router, temporary lifecycle shim, page hotfix scripts, and global task bridge from the active frontend path.
- Deleted scripts include `app-v2.js`, `route-lifecycle.js`, `*-hotfix.js`, root `task-store.js`, and `module-task-bridge.js`.

### Product Boundary
- This is an architecture refactor, not a new feature expansion.
- The frontend still uses mock/localStorage state until server persistence and real account permissions are added.
- Future updates should add or change one module at a time under `web_demo/modules/`.

## v1.2.0 - 2026-06-16

### Product Decision
- V1.2.0 upgrades the frontend from patch-style module observers to a unified route lifecycle coordinator.
- The product goal is stable fast module switching before adding accounts, permissions, realtime updates, or real platform connectors.
- Product truth: route transitions must be centrally scheduled; module scripts should not independently compete to render after every DOM mutation.

### Changed
- Added `web_demo/route-lifecycle.js` as the route lifecycle coordinator.
- `route-lifecycle.js` captures `hashchange` listeners and runs them through one scheduled route queue.
- Legacy hotfix `MutationObserver` callbacks are converted into route-after-render callbacks so they no longer fire on every DOM rewrite.
- `index.html` now loads `route-lifecycle.js` between `task-store.js` and `app-v2.js`.
- Frontend assets now use `?v=1.2.0`; API and health versions are aligned.

### Product Boundary
- This is a lifecycle governance layer over the current frontend modules.
- It stabilizes fast navigation and reduces observer loops, but it does not yet rewrite every page as a clean component module.
- The next deeper refactor should gradually move each hotfix page into explicit `render / mount / unmount` modules registered in the route registry.

## v1.1.2 - 2026-06-16

### Product Decision
- V1.1.2 fixes the fast module-switch crash introduced by observer-based task bridge binding.
- The issue was not script load order; it was a DOM observer loop inside `web_demo/module-task-bridge.js`.
- Product truth: bridge scripts may listen for module DOM changes, but repeated binding must be throttled and idempotent.

### Changed
- `module-task-bridge.js` now batches repeated `MutationObserver` callbacks through `requestAnimationFrame`.
- Button label, class, and title updates now only write to the DOM when the value truly changes.
- Fast module switching no longer causes the bridge to continuously rewrite the same buttons.
- Frontend assets now use `?v=1.1.2`; API and health versions are aligned.

### Product Boundary
- This still uses front-end mock persistence.
- The fix prevents render loops during rapid module navigation; it does not replace the later need for a cleaner component lifecycle or server-side task state.

## Earlier History

- v1.1.1: Added dedupe identity to task-store tasks.
- v1.1.0: Added unified front-end task store and dynamic module task flow.
- v1.0.24: 首页 became a command-board scheduling view.
- v1.0.23: 首页 became a cross-module task summary.
- v1.0.22: 报告 page became 日志 / operation log center.
- v1.0.21: 确认 page became 待办 / task center.
- v1.0.0-v1.0.20: Product trunk cleanup and page productization.
