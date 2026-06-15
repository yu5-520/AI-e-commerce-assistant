# Product Changelog

## v1.0.14 - 2026-06-15

### Product Decision
- Report pages must support both import and export as real actions.
- `导出报表` cannot remain a decorative button; it must generate a downloadable file for the visible report data.
- `下载模板` should also generate a usable local CSV template, not only show prompt text.
- Current product truth remains: `web_demo/index.html?v=1.0.14` → `web_demo/app-v2.js?v=1.0.14` + `web_demo/data-report-hotfix.js?v=1.0.14` → actionable report manager UI.

### Fixed
- `导出报表` now downloads the current report as a CSV file.
- Report manager cards now include `查看报表`、`导入数据`、`导出`.
- Report detail pages now include `导入报表` and functional `导出报表`.
- `下载模板` now downloads a CSV template for the selected report.
- Added operation notices so users can see when export/template/import actions have been triggered.
- `web_demo/index.html` now bumps frontend assets to `?v=1.0.14`.
- API version is aligned to `v1.0.14` for this product interaction fix.

### Product Boundary
- Export and template download are real local browser actions.
- Import remains a mock validation and confirmation flow until real ERP / CRM / 聚水潭 connectors are connected.
- Report contents are still Mock ERP / CRM data.

## v1.0.11 - 2026-06-15

### Product Decision
- The data page is now an ERP / CRM report-management page, not a black-box data-health page.
- The sidebar label should be `报表`, while the page title should clearly state `ERP / CRM 报表管理`.
- Report rows must be actionable: each report needs a `查看报表` entry that opens a detailed report view.
- Current product truth remains: `web_demo/index.html?v=1.0.11` → `web_demo/app-v2.js?v=1.0.11` + `web_demo/data-report-hotfix.js?v=1.0.11` → report manager UI.

### Changed
- Added `web_demo/data-report-hotfix.js` to replace the old data-health page after render.
- Added `web_demo/report-center.css` for report manager cards, detail pages, and report tables.
- The data navigation label is now `报表`.
- The page now shows ERP / CRM report groups with status, record counts, source labels, and `查看报表` buttons.
- Added drill-down pages for 商品报表、订单报表、库存报表、退款报表、客户报表、客户标签报表、客户互动报表.
- `web_demo/index.html` now bumps frontend assets to `?v=1.0.11` and loads the report manager hotfix script.
- API version is aligned to `v1.0.11` for this product surface update.

### Product Boundary
- This is a merchant-facing UI productization patch.
- Report contents are still Mock ERP / CRM data.
- Real 聚水潭、ERP、CRM、广告后台 connectors are future integrations, not active production connections.

## v1.0.10 - 2026-06-15

### Product Decision
- The operating unit page is a store-group management page, not an engineering category-recognition page.
- The page should show which platforms and shops are managed, what data is connected, and which systems can be connected next.
- Distribution and trigger-rule blocks should be removed from the visible operating-unit page because they do not help merchants manage store groups.
- Current product truth remains: `web_demo/index.html?v=1.0.10` → `web_demo/app-v2.js?v=1.0.10` + `web_demo/operating-unit-hotfix.js?v=1.0.10` → store-group operating unit UI.

### Changed
- Added `web_demo/operating-unit-hotfix.js` to replace the old operating-unit page after render.
- The page now shows `家居生活店铺组`, linked platforms, shop count, connected data, pending integrations, associated shops, and data-source status.
- `web_demo/dashboard.css` now includes store-group layout styles for hero, metric cards, shop rows, and data-source rows.
- `web_demo/index.html` now bumps frontend assets to `?v=1.0.10` and loads the operating-unit hotfix script after existing frontend scripts.
- API version is aligned to `v1.0.10` for this product surface update.

### Product Boundary
- This is a merchant-facing UI productization patch.
- Real 聚水潭、千牛、店铺后台、广告后台 connections are still future integrations, not active production connectors.
- The product still uses Mock ERP / CRM data.

## v1.0.9 - 2026-06-15

### Product Decision
- The screenshot showed the ECS/browser was still serving the old v1.0.7 dashboard hero, so the fix must cover both current code and cached old markup.
- The homepage must not show `今日任务清单` or `今日到期` after the compact task-list correction.
- Current product truth remains: `web_demo/index.html?v=1.0.9` → `web_demo/app-v2.js?v=1.0.9` + `web_demo/dashboard-hotfix.js?v=1.0.9` → `/api/business/today` compact task board payload.

### Fixed
- Added `web_demo/dashboard-hotfix.js` to patch stale dashboard DOM after render.
- The hotfix changes cached `今日任务清单` to `任务清单` and cached `今日到期` to `到期任务`.
- `web_demo/dashboard.css` now includes fallback styling for old `.hero-card.dashboard-hero` markup so the top module shrinks even when cached old JavaScript still renders it.
- `web_demo/index.html` now bumps all frontend assets to `?v=1.0.9` and loads the hotfix after the main app script.
- API version is aligned to `v1.0.9` for this cache-compatibility correction.

### Product Boundary
- This is a frontend cache/deployment hardening patch, not a workflow change.
- After deployment, the ECS must pull the latest commit; otherwise the browser will still see the old server files.

## v1.0.8 - 2026-06-15

### Product Decision
- The dashboard module bar must not dominate the first screen; task cards should be the main viewport content.
- The homepage title is `任务清单`, not `今日任务清单`; date and update time are small realtime metadata.
- Numbers are secondary distribution indicators. The ordered task queue is the primary product interaction surface.
- Visible frontend layout updates should carry asset query versions so old cached UI files do not keep showing removed dashboard blocks.
- Current product truth remains: `web_demo/index.html?v=1.0.8` → `web_demo/app-v2.js?v=1.0.8` → `/api/business/today` compact task board payload.

### Changed
- `web_demo/app-v2.js` now renders a compact dashboard status bar instead of the oversized hero card.
- The main dashboard title is fixed to `任务清单`; realtime date/update copy appears below as small status text.
- `web_demo/dashboard.css` now reduces header and metric card height so task cards occupy the main visual area.
- `/api/business/today` now returns `任务清单` and `到期任务` wording for the compact task-list contract.
- `web_demo/index.html` now appends `?v=1.0.8` to CSS and JS assets for cache busting.
- API smoke tests now verify the compact task-list title and distribution wording.
- API version is aligned to `v1.0.8` for this dashboard layout correction.

### Product Boundary
- The product still does not execute real shop operations.
- Confirmation remains a user decision record, not automated RPA execution.
- Homepage layout should express task priority and operating urgency before explanation, policy, or report-style wording.

## v1.0.7 - 2026-06-15

### Product Decision
- The homepage overview is an operations task board, not a single-theme analysis report.
- The primary homepage job is to show task order, urgency, deadline, item count, and operating impact.
- Internal boundary language should not be shown as a main dashboard module; merchant-facing confirmation and execution rules belong in the confirmation flow or API contract, not in the overview layout.
- Current product truth remains: `web_demo/index.html` → `web_demo/app-v2.js` → `/api/business/today` task board payload.

### Changed
- `/api/business/today` now returns `task_distribution` and `task_queue` for the homepage dashboard.
- `web_demo/app-v2.js` renders the hero title as `今日任务清单` instead of using the next internal module label as the page theme.
- The old homepage `下一步` bullet block was replaced by ordered task cards with urgency, deadline, count, impact, and reason.
- The old homepage `边界` card was removed from the dashboard rendering.
- Added `web_demo/dashboard.css` and loaded it from `web_demo/index.html` for the task board layout.
- API smoke tests now verify the task board contract and prevent `boundaries` from returning to the merchant overview payload.
- API version is aligned to `v1.0.7` for this dashboard contract update.

### Product Boundary
- The product still does not execute real shop operations.
- Confirmation remains a user decision record, not automated RPA execution.
- Safety rules can exist in product APIs as execution guidance, but the homepage must prioritize merchant execution order over engineering wording.

## v1.0.5 - 2026-06-15

### Product Decision
- Product-facing business APIs must expose the same state that users create through confirmation actions.
- Current product truth remains: `web_demo/app-v2.js` → `/api/business/*` → approval records only, no real RPA execution.

### Changed
- `/api/business/actions` now merges persisted approval status before returning action cards.
- `/api/health` now returns the current version and product name.
- Added `/api/system/clear-runtime-data` as the current runtime cleanup endpoint.
- Kept `/api/system/clear-demo-data` as a backward-compatible alias.
- API smoke tests now verify that approve/reject updates reappear through `/api/business/actions`.
- API version is aligned to `v1.0.5` for this backend API contract repair.

### Product Boundary
- Confirmation APIs record user decisions only; they do not execute real shop operations.
- Product APIs should reflect approval state without requiring the UI to call low-level approval records directly.

## v1.0.4 - 2026-06-15

### Product Decision
- The frontend UI now uses productized business API sections instead of behaving like a raw workflow viewer.
- Current product truth remains: `web_demo/index.html` → `web_demo/app-v2.js` → `/api/business/*`.

### Changed
- `web_demo/index.html` now loads only `styles.css` and `app-v2.js`.
- Sidebar hash routes now use clearer business section names for product pages.
- `web_demo/app-v2.js` now prefers dedicated product endpoints for product health, competitor opportunities, listing suggestions, traffic review, action confirmations, and reports.
- Data health status now renders `passed` as `通过`.
- API version is aligned to `v1.0.4` for this frontend UI cleanup.
- Governance now blocks the removed standalone data-import stylesheet from returning to active trunk.

### Removed From Active Product Trunk
- Removed `web_demo/data-import.css`.
- Removed the unused frontend import action from the current UI runtime.

### Product Boundary
- Frontend pages should present product API results, not internal workflow structure as the primary UI contract.
- Standalone UI components that are no longer used by the current page should be removed instead of kept as inactive styling residue.

## v1.0.3 - 2026-06-15

### Product Decision
- Active module memory now comes only from the current ERP operating-unit runtime path.
- The old standalone module-chain registry and obsolete module files are no longer part of active trunk.
- Current product truth remains: `src.api.main:app` → `/api/business/*` → `business_view_service` → `mock_workflow` → current ERP operating-unit modules.

### Changed
- Report generation now uses `src/reports/generate_operating_report.py`.
- Product report output now uses `outputs/operating_report.md`.
- Workflow documentation inside `mock_workflow.py` now points to FastAPI business APIs and smoke tests, not removed CLI demo entrypoints.
- API version is aligned to `v1.0.3` for this module-chain cleanup.
- Governance now blocks removed module-chain roots and old report naming from returning to active trunk.

### Removed From Active Product Trunk
- Removed `runtime/module_chain.json`.
- Removed obsolete module files under the old `modules/` tree.
- Removed `src/reports/generate_demo_report.py`.

### Product Boundary
- Future module chains must be connected to the current ERP operating-unit workflow before entering active trunk.
- Old prompt/module experiments should remain recoverable from Git history, not from current runtime folders.

## v1.0.2 - 2026-06-15

### Product Decision
- Active product docs now describe only the current ERP operating-unit workbench, not future multi-page product blueprints.
- Current product truth remains: `src.api.main:app` → `/api/business/*` → `web_demo/index.html` + `web_demo/app-v2.js`.
- Future product maps or multi-page flows must be created as clearly marked proposals, not as current MVP docs.

### Changed
- Rewrote README product-doc rules so product changelog, decision log, and cleanup log have distinct responsibilities.
- Rewrote `docs/product/README.md` to list only the active current product docs.
- Rewrote `docs/product/mvp-scope.md` around the current `/api/business/*` MVP and current smoke-test commands.
- Rewrote `docs/product/module-boundary.md` around current API, workflow, frontend, scripts, CI, and documentation boundaries.
- Extended version governance so active docs are checked for stale legacy snippets.
- API version is aligned to `v1.0.2` for this documentation-trunk cleanup.

### Removed From Active Product Docs
- Removed `docs/product/product-map.md`.
- Removed `docs/product/user-flow.md`.
- Removed `docs/product/domain-model.md`.

### Product Boundary
- Active docs must not describe removed routes, old demo commands, old Agent chains, or future pages as current reality.
- Current docs should protect the runnable product trunk from being pulled back into obsolete structures.

## v1.0.1 - 2026-06-15

### Product Decision
- The active product trunk no longer carries the old Material Observer Agent layer.
- The product script chain now treats version governance as a required CI gate before runtime and API smoke tests.
- The current product path remains the AI ERP operating-unit workbench: `src.api.main:app` → `/api/business/*` → `web_demo/app-v2.js`.

### Changed
- GitHub Actions now validates the current trunk with `scripts/check_version_governance.py`, `scripts/smoke_test_runtime.py`, and `scripts/smoke_test_api.py`.
- API version is aligned to `v1.0.1` for this script-chain repair.

### Removed From Active Product Trunk
- Removed the old Material Observer Agent files and runtime registry.
- Historical agent work remains recoverable from Git history, but it is no longer part of the active product surface.

### Product Boundary
- Future product-structure changes must update product changelog and versioning changelog together.
- CI must fail when current version, FastAPI app version, and version logs are not aligned.

## v1.0.0 - 2026-06-15

### Product Decision
- The active product trunk is now the AI ERP operating-unit workbench, not the earlier title/image generation or material-observation demo flow.
- The current user-facing path is `web_demo/index.html` + `web_demo/app-v2.js`, backed by `/api/business/*`.
- The product story is now centered on ERP-inferred operating units, cycle frequency, product health, competitor opportunities, listing suggestions, traffic review, confirmation actions, and business reports.

### Changed
- Main branch now keeps one current runnable product path.
- README and versioning records now describe the current AI ERP operating-unit product architecture.
- API surface is narrowed to the product-facing business routes plus health, data import, approval, and system maintenance routes.
- API version is aligned to `v1.0.0` as the first cleaned product trunk version.

### Removed From Active Product Trunk
- Old frontend template: `web_demo/app.js`.
- Legacy compatibility route families: `/api/demo`, `/api/products`, `/api/customers`, `/api/diagnosis`, `/api/tasks`, `/api/reports`, `/api/evals`, and `/api/logs`.
- Old standalone helpers: `src/run_demo.py`, `src/services/workflow_service.py`, and `evals/run_evals.py`.

### Product Boundary
- The product still uses Mock ERP / CRM data.
- The product does not connect to real shop backends.
- The product does not automatically change prices, publish listings, launch ad campaigns, message customers, or process refunds.
- High-risk actions remain confirmation records only.

### Follow-up
- Future product updates that change page structure, active route families, workflow stages, or product positioning must update this file and `versioning/CHANGELOG.md` together.
