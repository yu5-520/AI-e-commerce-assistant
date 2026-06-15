# Changelog

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

## v1.0.24 - 2026-06-15

### Changed
- Simplified the homepage `任务清单` into a command-board style scheduling and navigation view.
- Reworked `web_demo/dashboard-hotfix.js` so homepage task data now uses short task types, product short names, source modules, time buckets, and judgment tags instead of long handling explanations.
- Reworked `web_demo/dashboard-linked.css` so task rows are compact scheduling rows instead of large detail cards.
- Added a `时间系统` strip that groups active tasks by deadline buckets such as `今天 18:00 前`, `今天内`, `明天前`, and `本周内`.
- Homepage cards now emphasize `排序号 / 优先级 / 截止时间 / 来源 / 判断标签 / 导航按钮`.
- Reduced homepage actions to navigation-first controls: `进入待办`, `查看来源`, `商品`, and a weaker `完成` action.
- `web_demo/index.html` now appends `?v=1.0.24` to assets.
- Aligned the FastAPI app version and health version with the repository version: `1.0.24`.

### Product Engineering Rule
- 首页 is a command board, not an execution page.
- Long reasons and detailed handling text belong in 待办, not on the 首页.
- 首页 should highlight task order, navigation, time, and judgment signals.

## v1.0.23 - 2026-06-15

### Changed
- Upgraded the homepage `任务清单` from a standalone static task board into a cross-module task summary.
- Replaced the old dashboard hotfix with a linked dashboard task pool covering 商品、竞品、上新、流量、报表、待办 and 日志.
- Added `web_demo/dashboard-linked.css` for linked dashboard task cards, source buttons, product context, and responsive layout.
- Homepage metrics are now calculated from active tasks: 紧急任务、到期任务、待确认、可测试机会.
- Each homepage task now shows precise product/store context, source module, deadline, reason, and impact.
- Each task exposes `进入待办`, `查看来源`, `查看商品`, and `标记完成` actions.
- Completed items are removed from the homepage task summary and represented as log-trace behavior.
- `web_demo/index.html` now appends `?v=1.0.23` to assets and loads the linked dashboard stylesheet.
- Aligned the FastAPI app version and health version with the repository version: `1.0.23`.

### Product Engineering Rule
- The homepage is not a second full task center. It should show only the top cross-module tasks that need attention now.
- The 待办 page remains the full task queue, while the 首页 is the executive summary.
- Every homepage task must link back to its source module and show the affected product/store or report context.
- Completed tasks should leave the homepage and be traceable through 日志.

## v1.0.22 - 2026-06-15

### Changed
- Repositioned the old `报告` page as `日志` / operation log center.
- Changed the sidebar label from `报告` to `日志` while keeping the existing `#business-report` route for compatibility.
- Added `web_demo/log-manager-hotfix.js` with operation logs for task completion, AI judgment, data import/export, and user actions.
- Added `web_demo/log-center.css` for log rows, metrics, filters, detail pages, source jumps, export action, and responsive layout.
- Removed the visible Markdown-style report panel from the user-facing page; logs now show productized records with time, type, source, status, product/store context, action, reason, and result.
- Added filters for type, source, and status, plus search across log content and export of the currently filtered logs.
- Added log detail page, source jump, related-task jump, and CSV export of the filtered logs.
- `web_demo/index.html` now appends `?v=1.0.22` to assets and loads the operation log center script.
- Aligned the FastAPI app version and health version with the repository version: `1.0.22`.

### Product Engineering Rule
- Reports are user-facing conclusions; logs are trace records of what the system and user already did.
- The log page should support追溯: when, what source, which product/store, what action, why it happened, and what result was produced.
- Log pages should not become primary decision pages; they should link back to source modules and related tasks.

## v1.0.21 - 2026-06-15

### Changed
- Repositioned the old `确认` page as `待办任务` / task center.
- Changed the sidebar label from `确认` to `待办` while keeping the existing `#business-actions` route for compatibility.
- Added `web_demo/todo-manager-hotfix.js` with tasks generated from 商品、竞品、上新、流量、报表 and AI 自动判定.
- Added `web_demo/todo-center.css` for task-center cards, metrics, filters, deadline ordering, detail pages, and responsive layout.
- Tasks now include precise product or report context: image placeholder, title, platform, shop, link, source module, priority, deadline, reason, status, and actions.
- Task cards are sorted by deadline/urgency and expose task-specific actions instead of generic `确认 / 拒绝` only.
- Added filters for source, status, and priority, plus search across task, product, source, deadline, and reason.
- Added task detail page and source jump actions.
- `web_demo/index.html` now appends `?v=1.0.21` to assets and loads the todo task center script.
- Aligned the FastAPI app version and health version with the repository version: `1.0.21`.

### Product Engineering Rule
- The actions page is not a system-action approval list; it is the full task queue generated by other modules and AI judgment.
- Task rows must show what to do, by when, why it exists, which module created it, and which product/store it affects.
- The overview page should show only top tasks; the 待办 page is the complete execution queue.

## Earlier History

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
