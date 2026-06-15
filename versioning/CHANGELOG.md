# Changelog

## v1.0.14 - 2026-06-15

### Fixed
- Made `导出报表` functional in the ERP / CRM report center.
- Report manager and report-detail pages now download CSV files from the visible report table data.
- `下载模板` now creates a CSV template file instead of only showing an alert.
- Report manager now exposes `导入报表`, `下载模板`, and `导出当前报表` as concrete actions.
- Per-report cards now expose `查看报表`, `导入数据`, and `导出` actions.
- `web_demo/index.html` now appends `?v=1.0.14` to assets and reloads the fixed report workflow.
- Aligned the FastAPI app version and health version with the repository version: `1.0.14`.

### Product Engineering Rule
- Buttons shown in a product UI must either perform an action or be visibly disabled; no inert action buttons on user-facing pages.
- Export should generate a local file immediately for the currently selected report.
- Import remains a field-check and confirmation flow until real ERP / CRM / 聚水潭 connectors are connected.

## v1.0.13 - 2026-06-15

### Changed
- Added user-driven report import to the ERP / CRM report center.
- Report manager now shows a primary `导入报表` action and per-report `导入数据` actions next to `查看报表`.
- Report detail pages now show `导入报表` next to `重新同步` and `导出报表`.
- Added local CSV/XLS/XLSX file selection, required-field checklist, template prompt, and mock import confirmation flow.
- Extended `web_demo/report-center.css` with import toolbar, import panel, file-drop area, import status, and responsive import controls.
- `web_demo/index.html` now appends `?v=1.0.13` to assets and reloads the report import workflow.
- Aligned the FastAPI app version and health version with the repository version: `1.0.13`.

### Product Engineering Rule
- Report pages must support both import and export. Export is for taking data out; import is for users to refresh or add report data before full ERP / 聚水潭 integration exists.
- Manual import should validate fields first and then enter a confirmation flow, rather than silently replacing report data.
- Future real connectors can replace the mock import confirmation without changing the merchant-facing report workflow.

## v1.0.11 - 2026-06-15

### Changed
- Renamed the visible data navigation concept into a report-management surface: `ERP / CRM 报表管理`.
- Added `web_demo/data-report-hotfix.js` so the old static data-health page is replaced after render with ERP/CRM report groups and clickable report cards.
- Added `web_demo/report-center.css` for report hero, report cards, drill-down actions, and table detail layouts.
- Added report drill-down pages for 商品报表、订单报表、库存报表、退款报表、客户报表、客户标签报表、客户互动报表.
- `web_demo/index.html` now appends `?v=1.0.11` to assets, renames the sidebar item from 数据 to 报表, and loads the report manager hotfix script.
- Aligned the FastAPI app version and health version with the repository version: `1.0.11`.

### Product Engineering Rule
- The report page should answer: where the data comes from, how many records are available, and what report can be opened next.
- Data-health checks are internal support signals; merchants need report cards and detailed tables, not static pass/fail rows.
- Report detail pages should use product terms such as 商品报表 and 订单报表 instead of database/table wording.

## v1.0.10 - 2026-06-15

### Changed
- Productized the operating unit page from an ERP/category recognition panel into a store-group management surface.
- Added `web_demo/operating-unit-hotfix.js` so the page now shows platform count, shop count, connected data types, pending integrations, associated shops, and data-source status.
- Removed visible dependence on engineering category fields such as `sun_protection_goods`, `home_storage_goods`, distribution blocks, and trigger-rule blocks from the operating-unit user experience.
- Extended `web_demo/dashboard.css` with store-group layout styles for the operating unit hero, metrics, shop rows, and data-source rows.
- `web_demo/index.html` now appends `?v=1.0.10` to assets and loads the operating-unit hotfix script after the dashboard hotfix.
- Aligned the FastAPI app version and health version with the repository version: `1.0.10`.

### Product Engineering Rule
- The operating unit page should answer: which platforms and shops are managed, what data is connected, and which systems can be connected next.
- Engineering category IDs and trigger rules belong in backend diagnosis, not in the merchant-facing operating-unit page.
- Store group is the product anchor: 店铺群 → ERP/CRM/聚水潭 → 商品/库存/售后/流量 → 任务清单。

## v1.0.9 - 2026-06-15

### Fixed
- Added `web_demo/dashboard-hotfix.js` to patch cached v1.0.7 dashboard markup after render.
- The hotfix changes stale `今日任务清单` text to `任务清单` and stale `今日到期` text to `到期任务` when an older cached dashboard script is still running.
- Added compatibility CSS for `.hero-card.dashboard-hero` so the old oversized hero layout is compacted even if cached JavaScript still emits the old hero markup.
- `web_demo/index.html` now appends `?v=1.0.9` to CSS and JS assets and loads the dashboard hotfix script after `app-v2.js`.
- Aligned the FastAPI app version and health version with the repository version: `1.0.9`.

### Product Engineering Rule
- Visible dashboard layout fixes must include both the current render path and a cache-compatibility path when the browser may still hold older JavaScript.
- If the server shows old UI after a repository update, first verify whether the ECS instance has pulled the latest commit and whether the browser is still using cached frontend assets.

## v1.0.8 - 2026-06-15

### Changed
- Compact dashboard header now uses `任务清单` as the main title and moves realtime date/update copy into a small label.
- Replaced the oversized hero-card dashboard layout with a compact status bar so the task queue gets the primary viewport.
- Reduced dashboard metric card height and typography so numbers support the task list instead of dominating the page.
- `/api/business/today` now uses `任务清单` and `到期任务` wording instead of date-prefixed dashboard titles.
- `web_demo/index.html` now appends `?v=1.0.8` to frontend assets to reduce stale browser cache after deployment.
- API smoke tests now assert compact task-list naming and dashboard metric wording.
- Aligned the FastAPI app version and health version with the repository version: `1.0.8`.

### Product Engineering Rule
- The overview title area should stay compact; the task list is the homepage's main visual weight.
- Date and update time should appear as small status metadata, not as the core dashboard title.
- Asset URLs should be versioned when visible frontend layout changes are pushed to avoid old cached JavaScript and CSS being served.

## v1.0.7 - 2026-06-15

### Changed
- Repositioned the homepage overview as a merchant-facing task board instead of a single analysis-theme page.
- `/api/business/today` now exposes `task_distribution`, `task_queue`, and `execution_rules` for ordered dashboard rendering.
- `web_demo/app-v2.js` now renders the dashboard as a dated task list with urgency, deadline, item count, impact, and reason fields.
- Added `web_demo/dashboard.css` for dashboard task queue layout and loaded it from `web_demo/index.html`.
- Updated API smoke tests so the current dashboard contract checks task distribution and ordered task queue, and blocks internal `boundaries` wording from returning to the merchant overview contract.
- Aligned the FastAPI app version and health version with the repository version: `1.0.7`.

### Product Engineering Rule
- The homepage overview should answer: what to do first, by when, how many items are involved, and why it matters.
- Internal safety/boundary language should not occupy the merchant dashboard. User-facing execution rules can remain in API payloads, but the homepage should prioritize task order and operating urgency.

## v1.0.6 - 2026-06-15

### Fixed
- Fixed the FastAPI server import failure on the homepage route.
- Disabled response model generation for `/` with `response_model=None`.
- Replaced the invalid homepage return annotation with `Any` so FastAPI no longer tries to build a Pydantic model from `FileResponse | Dict`.
- Aligned the FastAPI app version and health version with the repository version: `1.0.6`.

### Product Engineering Rule
- Routes that can return `FileResponse` should not expose mixed response type annotations as FastAPI response models.
- Server import checks should be run after endpoint signature changes.

## v1.0.5 - 2026-06-15

### Fixed
- Repaired the backend API contract for approval status roundtrip.
- `/api/business/actions` now merges persisted approval status from the approval service before returning product-facing action cards.
- `/api/health` now returns the current API version and product name instead of a generic text label.
- Added `/api/system/clear-runtime-data` as the current system cleanup endpoint while keeping `/api/system/clear-demo-data` as a backward-compatible alias.
- Strengthened `scripts/smoke_test_api.py` so CI verifies approve/reject state is visible again through `/api/business/actions`.
- Aligned the FastAPI app version with the repository version: `version="1.0.5"`.

### Product Engineering Rule
- Approval state must be visible through product-facing business APIs, not only through low-level approval endpoints.
- Health output must reflect the current application version.
- New endpoint names should use current product terminology; legacy names may remain only as compatibility aliases.

## v1.0.4 - 2026-06-15

### Changed
- Aligned the frontend UI with the productized `/api/business/*` API surface.
- `web_demo/app-v2.js` now uses dedicated product endpoints for product health, competitor opportunities, listing suggestions, traffic review, action confirmations, and business reports.
- `web_demo/index.html` now uses clearer business hash sections such as `#business-products`, `#business-traffic`, and `#business-report`.
- Removed the unused import action from the frontend runtime.
- Added a Chinese label for `passed` data-health status.
- Aligned the FastAPI app version with the repository version: `version="1.0.4"`.
- Extended `scripts/check_version_governance.py` so the removed standalone data-import stylesheet cannot return to active trunk.

### Removed
- Removed `web_demo/data-import.css` from active trunk.

### Product Engineering Rule
- Frontend pages should prefer productized `/api/business/*` endpoints instead of rendering directly from raw workflow internals.
- Removed frontend components should be blocked by version governance, not only deleted once.

## v1.0.3 - 2026-06-15

### Changed
- Removed the old module-chain memory layer from the active product trunk.
- Added `src/reports/generate_operating_report.py` and updated workflow/service imports to use the current operating report output.
- `src/workflow/mock_workflow.py` now describes itself as the FastAPI business API and smoke-test orchestration layer, not a removed CLI demo layer.
- `src/services/business_view_service.py` now reads `outputs/operating_report.md`.
- Aligned the FastAPI app version with the repository version: `version="1.0.3"`.
- Extended `scripts/check_version_governance.py` so removed module-chain roots and old report naming cannot return to active trunk.

### Removed
- Removed `runtime/module_chain.json`.
- Removed obsolete module files under the old `modules/` tree from active trunk.
- Removed `src/reports/generate_demo_report.py`.

### Product Engineering Rule
- Active module memory must come from the real runtime chain: `src.api.main:app` → `/api/business/*` → `business_view_service` → `mock_workflow` → current ERP operating-unit modules.
- Old module registries should live in Git history, not in active trunk.
- Report modules must use current product naming, not old demo naming.

## v1.0.2 - 2026-06-15

### Changed
- Cleaned the active documentation trunk so current docs describe only the v1.x ERP operating-unit product path.
- Updated README and `docs/product/README.md` to use the same product-log rules and current file map.
- Rewrote `docs/product/mvp-scope.md` around the current single-page product, `/api/business/*`, and current smoke tests.
- Rewrote `docs/product/module-boundary.md` around current API, workflow, frontend, scripts, CI, and documentation boundaries.
- Extended `scripts/check_version_governance.py` so active docs are checked for stale legacy snippets.
- Aligned the FastAPI app version with the repository version: `version="1.0.2"`.

### Removed
- Removed outdated planning documents from the active product docs: `docs/product/product-map.md`, `docs/product/user-flow.md`, and `docs/product/domain-model.md`.

### Product Engineering Rule
- Active docs must describe the current runnable trunk, not future blueprints or deleted route families.
- Future planning belongs in a new clearly marked proposal document, not in current MVP docs.
- Version governance must fail if active docs reintroduce stale commands such as old demo runs or removed route checks.

## v1.0.1 - 2026-06-15

### Fixed
- Repaired the GitHub Actions script chain so CI checks the current product trunk instead of deleted legacy entrypoints.
- `.github/workflows/runtime-smoke-test.yml` now runs syntax checks, `scripts/check_version_governance.py`, `scripts/smoke_test_runtime.py`, and `scripts/smoke_test_api.py`.
- Added `scripts/check_version_governance.py` to enforce version/log consistency before smoke tests run.
- Aligned the FastAPI app version with the repository version: `version="1.0.1"`.

### Removed
- Removed legacy Agent files from the active product trunk.
- Historical agent work remains recoverable from Git history, but it is no longer part of the current v1.x ERP operating-unit product path.

### Product Engineering Rule
- CI must run the version governance check before smoke tests.
- If a future cleanup removes routes, folders, workflows, or product entrypoints, the same change must update `versioning/VERSION.md`, `versioning/CHANGELOG.md`, and `docs/product/CHANGELOG.md`.

## v1.0.0 - 2026-06-15

### Changed
- Recut the repository into a single current product trunk: `src.api.main:app` → `/api/business/*` → `web_demo/app-v2.js`.
- Updated `src/api/main.py` so it only mounts the current product-facing API surface plus health, data import, approval, and system maintenance routes.
- Updated `scripts/start_server.sh` to default to `127.0.0.1:3000`, keeping public access behind Nginx.
- Rewrote `README.md` around the current AI ERP operating-unit product architecture and deployment path.
- Updated `scripts/smoke_test_api.py` so API smoke tests verify only current product routes.
- Added `docs/product/CHANGELOG.md` as the product-level log for positioning, page/API boundary, and active trunk changes.

### Removed
- Removed the old frontend template, legacy compatibility routes, and old helper entrypoints that pulled the project back toward the previous demo shape.

### Added
- Added `.gitignore` rules for runtime outputs, local logs, local databases, virtual environments, and environment files.

### Product Engineering Rule
- The main branch should contain only the current runnable product path.
- Old demo templates, legacy compatibility APIs, and deprecated run commands should live in Git history, not in the active product trunk.
- Every architecture-level cleanup must update this `versioning/` record and the relevant product log under `docs/product/`.

## Earlier History

- v0.9.2: Agent module governance was added.
- v0.9.1: Material observation was moved back into an implicit backend pipeline.
- v0.9.0: Pre-generation material sampling UI was added.
- v0.8.9: Light material observation Agent layer was added.
