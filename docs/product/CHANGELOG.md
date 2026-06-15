# Product Changelog

## v1.0.17 - 2026-06-15

### Product Decision
- The 商品 page should use responsive product cards at tablet widths instead of forcing a dense table layout.
- Product title readability comes before column density: title, platform/shop, metrics, and actions should be separate visual areas.
- `全部平台`、`全部店铺`、`状态` controls must open selectable menus and change the visible product list.
- Current product truth remains: `web_demo/index.html?v=1.0.17` → `web_demo/product-manager-hotfix.js?v=1.0.17` + `web_demo/product-center.css?v=1.0.17` → responsive product cards with working filters.

### Changed
- Product rows now render as card rows instead of table rows.
- Long titles remain readable inside the product title block while metrics sit in a separate operation strip.
- Platform, store, and status filters now open option menus and filter the product list.
- Added search across product title, product ID, platform, store, inventory status, and after-sales status.
- 商品列表 count now reflects the active filters.
- `web_demo/index.html` now bumps frontend assets to `?v=1.0.17`.
- API version is aligned to `v1.0.17` for this product interaction and layout update.

### Product Boundary
- This is a frontend product-list interaction patch.
- Product data, links, inventory, and after-sales status are still Mock ERP / CRM data until real shop connectors are attached.

## v1.0.16 - 2026-06-15

### Product Decision
- Product list titles must be readable without damaging the table layout.
- Long titles should be clamped in the list view and fully visible in the detail view.
- The 商品 page should never allow product title text to overlap platform, shop, inventory, price, margin, after-sales, or action columns.
- Current product truth remains: `web_demo/index.html?v=1.0.16` → `web_demo/product-center.css?v=1.0.16` → compact product list with clamped titles.

### Fixed
- Product titles now clamp to two lines in the product list.
- Product row grid children now use `min-width: 0` so text shrinks inside its own cell.
- Store/status fields now ellipsize instead of being pushed by long product titles.
- Product action column was narrowed so the title column gets more stable room.
- `web_demo/index.html` now bumps frontend assets to `?v=1.0.16`.
- API version is aligned to `v1.0.16` for this product layout fix.

### Product Boundary
- This is a frontend layout fix.
- Product titles, links, inventory, and after-sales values are still Mock ERP / CRM data until real shop connectors are attached.

## v1.0.15 - 2026-06-15

### Product Decision
- The 商品 page is now a goods-operation list, not an oversized diagnosis-card page.
- Each product row must identify the real shop item through main image, title, platform, shop, and link.
- Inventory and after-sales risks should be shown on the affected fields, not as ambiguous `中` / `高` badges beside the product name.
- Current product truth remains: `web_demo/index.html?v=1.0.15` → `web_demo/app-v2.js?v=1.0.15` + `web_demo/product-manager-hotfix.js?v=1.0.15` → compact product manager UI.

### Changed
- Added `web_demo/product-manager-hotfix.js` to replace the old product diagnosis page after render.
- Added `web_demo/product-center.css` for compact product rows, product detail view, color-coded inventory/after-sales states, and responsive controls.
- The product page now shows platform, shop, full product title, image placeholder, link, inventory, price, margin, after-sales status, and actions.
- Product rows now expose `详情`, `复制链接`, and `商品报表` actions.
- Product detail page now shows a larger image placeholder, product link, store/platform context, inventory, price, margin, after-sales, and processing suggestion.
- `web_demo/index.html` now bumps frontend assets to `?v=1.0.15` and loads the product manager script.
- API version is aligned to `v1.0.15` for this product surface update.

### Product Boundary
- This is a merchant-facing UI productization patch.
- Product links are mock links until real shop platform connectors are attached.
- Inventory and after-sales states are Mock ERP / CRM values.

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
