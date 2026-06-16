# Changelog

## v1.3.0 - 2026-06-16

### Added
- Added modular frontend structure:
  - `web_demo/core/mock-data.js`
  - `web_demo/core/shell.js`
  - `web_demo/core/router.js`
  - `web_demo/core/task-actions.js`
  - `web_demo/stores/task-store.js`
  - `web_demo/modules/*/page.js`
  - `web_demo/bootstrap.js`
- Added page modules for dashboard, operating unit, report, product, competitor, listing, traffic, todo, and log routes.
- Added a route registry so pages register themselves through `AppRouter.register(page)` and render through one router lifecycle.

### Changed
- `web_demo/index.html` now loads only the modular frontend entry chain and uses `?v=1.3.0`.
- `task-store` moved into `web_demo/stores/task-store.js` while keeping `window.OPERATION_TASK_STORE` compatibility.
- Task generation moved from global DOM bridge behavior into `web_demo/core/task-actions.js` and module-local event binding.
- FastAPI app version and health version are aligned to `1.3.0`.

### Removed
- Removed legacy root task store: `web_demo/task-store.js`.
- Removed legacy router shell: `web_demo/app-v2.js`.
- Removed temporary lifecycle shim: `web_demo/route-lifecycle.js`.
- Removed legacy hotfix scripts:
  - `web_demo/dashboard-hotfix.js`
  - `web_demo/operating-unit-hotfix.js`
  - `web_demo/data-report-hotfix.js`
  - `web_demo/product-manager-hotfix.js`
  - `web_demo/competitor-manager-hotfix.js`
  - `web_demo/listing-manager-hotfix.js`
  - `web_demo/traffic-manager-hotfix.js`
  - `web_demo/todo-manager-hotfix.js`
  - `web_demo/log-manager-hotfix.js`
- Removed legacy global task bridge: `web_demo/module-task-bridge.js`.

### Product Engineering Rule
- New frontend features should be added as route modules under `web_demo/modules/<name>/page.js`.
- Shared state belongs in `web_demo/stores/`.
- Shared page shell and routing logic belongs in `web_demo/core/`.
- Modules must not own global `hashchange` listeners or global `MutationObserver` loops.
- Each module owns its own `render / mount / unmount` boundary through the router context.

## v1.2.0 - 2026-06-16

### Added
- Added `web_demo/route-lifecycle.js` as the unified front-end route lifecycle coordinator.
- Hash route listeners are now centrally registered and scheduled instead of each script owning an independent route listener.
- Legacy `MutationObserver` hotfix callbacks are converted into route-after-render callbacks through the lifecycle coordinator.
- Added route lifecycle hooks: `beforeRoute`, `afterRoute`, `runAfterRender`, and `schedule`.

### Changed
- `web_demo/index.html` now loads `route-lifecycle.js` after `task-store.js` and before `app-v2.js` / page modules.
- Frontend assets were bumped to `?v=1.2.0`.
- FastAPI app version and health version are aligned to `1.2.0`.

### Product Engineering Rule
- The router is the only place that should coordinate page transitions.
- Module scripts may still expose render and bind functions, but route changes must pass through the lifecycle queue.
- Observer-based hotfixes are now lifecycle-scheduled to prevent fast module switching from creating DOM rewrite loops.
- This version is an architecture-governance step before later account, permission, realtime, and API connector work.

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

## Earlier History

- v1.1.1: Added task identity and dedupe keys for same-product same-problem task merging.
- v1.1.0: Added unified front-end task store and dynamic module-driven task flow.
- v1.0.24: Dashboard task board was simplified into a command-board scheduling view with short judgment tags.
- v1.0.23: Dashboard task board linked the homepage to a cross-module task pool.
- v1.0.22: Report page became 日志 / operation log center.
- v1.0.21: Actions page became 待办任务 / task center.
- v1.0.0-v1.0.20: Product trunk cleanup and page-level productization.
