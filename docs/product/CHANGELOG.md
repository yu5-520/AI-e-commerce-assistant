# Product Changelog

## v1.0.18 - 2026-06-15

### Product Decision
- The 竞品 page should use the same scan pattern as the 商品 page: image, title, platform, store, link, core metrics, status, and actions.
- Competitor analysis should be a list of comparable competitor goods, not a single backend conclusion page.
- Engineering codes such as `below_market` must be translated into business wording before they reach the merchant-facing UI.
- Current product truth remains: `web_demo/index.html?v=1.0.18` → `web_demo/competitor-manager-hotfix.js?v=1.0.18` + `web_demo/competitor-center.css?v=1.0.18` → responsive competitor observation list.

### Changed
- Added `web_demo/competitor-manager-hotfix.js` to replace the old competitor analysis page after render.
- Added `web_demo/competitor-center.css` for responsive competitor rows, filter menus, metric strips, opportunity blocks, and detail pages.
- The competitor page now shows 8 comparable competitor items instead of one narrow analysis block.
- Competitor cards now show title, image placeholder, platform, store, link, price, monthly sales, rating, bad-review keywords, opportunity point, and actions.
- Added platform, target product, and status filters, plus competitor search.
- Added `详情`, `复制链接`, and `加入观察` actions.
- `web_demo/index.html` now bumps frontend assets to `?v=1.0.18` and loads the competitor manager script.
- API version is aligned to `v1.0.18` for this product surface update.

### Product Boundary
- This is a merchant-facing UI productization patch.
- Competitor links, sales, ratings, and review keywords are Mock data until real marketplace or crawler connectors are attached.
- `加入观察` is a local confirmation-style interaction, not a real external platform subscription.

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

## Earlier History

- v1.0.14: Report pages support real export and template download.
- v1.0.11: Data page became ERP / CRM report management.
- v1.0.10: Operating unit page became store-group management.
- v1.0.9: Added dashboard cache hotfix and compatibility CSS.
- v1.0.8: Compact dashboard task board was added.
- v1.0.7: Homepage overview was repositioned as a task board.
- v1.0.0-v1.0.6: Product trunk cleanup, API alignment, health/version repair, and current route governance.
