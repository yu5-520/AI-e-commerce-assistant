# Changelog

## v1.0.18 - 2026-06-15

### Changed
- Productized the 竞品 page from an analysis result panel into a competitor observation list aligned with the 商品 page structure.
- Added `web_demo/competitor-manager-hotfix.js` with eight mock competitor records, business-language price positions, platform/store/title/link fields, metrics, opportunity points, and detail views.
- Added `web_demo/competitor-center.css` for responsive competitor card rows, metric strips, opportunity blocks, filter menus, and detail pages.
- Removed visible engineering wording such as `below_market`; pricing is now shown as `低于市场价`、`高于市场价`、`接近市场价`.
- Added interactive filters for platform, target product, and status, plus search across competitor title, platform, store, bad-review keywords, and opportunity points.
- `web_demo/index.html` now appends `?v=1.0.18` to assets and loads the competitor manager script.
- Aligned the FastAPI app version and health version with the repository version: `1.0.18`.

### Product Engineering Rule
- Competitor pages should mirror product pages: title, image, platform, store, link, core metrics, status, and actions belong in the same scan-friendly row pattern.
- Engineering enum values must be translated before reaching the merchant-facing UI.
- Competitor analysis should show multiple comparable items, not a single backend conclusion block.

## v1.0.17 - 2026-06-15

### Changed
- Switched the 商品 page from forced table columns to responsive product cards so long product titles no longer collapse into unreadable vertical text.
- Product rows now show the product title block, platform/shop context, operation metrics, and actions as separate card areas instead of squeezed table cells.
- `全部平台`, `全部店铺`, and status controls are now interactive filter buttons with selectable option menus.
- Added product search for title, ID, platform, store, inventory status, and after-sales status.
- Filtered product counts now update in the 商品列表 header.
- `web_demo/index.html` now appends `?v=1.0.17` to assets and reloads the responsive product card workflow.
- Aligned the FastAPI app version and health version with the repository version: `1.0.17`.

### Product Engineering Rule
- Product list pages should use card rows at tablet widths; dense table columns are only safe when the viewport can protect every field.
- Filter controls must change visible data or open a selector. Decorative filters are not allowed on user-facing pages.

## v1.0.16 - 2026-06-15

### Fixed
- Fixed long product titles overlapping adjacent table columns on the 商品 page.
- Product title cells now use two-line clamping inside their own grid cell.
- Product row children now use `min-width: 0` so grid cells shrink correctly instead of spilling into the next column.
- Store/status cells now use ellipsis for overflow text.
- Product action column width was reduced so the product title column has more stable room.
- `web_demo/index.html` now appends `?v=1.0.16` to assets to avoid cached overlapping layouts.
- Aligned the FastAPI app version and health version with the repository version: `1.0.16`.

### Product Engineering Rule
- Long ecommerce titles should be clamped in list views and fully shown in detail views.
- Product list layout must protect neighboring fields: title, store, inventory, price, margin, after-sales, and actions should never visually overlap.

## v1.0.15 - 2026-06-15

### Changed
- Productized the 商品 page from oversized diagnosis cards into a compact goods-operation list.
- Added `web_demo/product-manager-hotfix.js` so the product route now shows main image placeholder, full product title, platform, shop, product link, inventory, price, margin, after-sales status, and row actions.
- Added `web_demo/product-center.css` for compact product rows, colored inventory/after-sales states, product detail view, and responsive actions.
- Removed visible ambiguous `中` / `高` risk badges from the product list; inventory and after-sales states are now shown directly in the relevant fields.
- Product rows now support `详情`, `复制链接`, and `商品报表` actions.
- `web_demo/index.html` now appends `?v=1.0.15` to assets and loads the product manager script.
- Aligned the FastAPI app version and health version with the repository version: `1.0.15`.

### Product Engineering Rule
- Product pages should show specific shop goods, not abstract analysis cards.
- Product list rows must include store, platform, title, image, link, and operational fields so merchants can identify the real item.
- Risk should be expressed on the affected field, such as inventory number or after-sales status, instead of generic severity badges.

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

## Earlier History

- v1.0.13: Report center added user-driven report import.
- v1.0.11: Data page was renamed and productized into `ERP / CRM 报表管理`.
- v1.0.10: Operating unit page was productized into a store-group management surface.
- v1.0.9: Added dashboard cache hotfix and compatibility CSS.
- v1.0.8: Compact dashboard task board was added.
- v1.0.7: Homepage overview was repositioned as a task board.
- v1.0.6: Fixed FastAPI homepage response model import failure.
- v1.0.5: Repaired approval status roundtrip and health version output.
- v1.0.4: Frontend UI was aligned with productized `/api/business/*` endpoints.
- v1.0.3: Removed old module-chain memory layer from active trunk.
- v1.0.2: Cleaned active documentation trunk.
- v1.0.1: Repaired GitHub Actions script chain.
- v1.0.0: Recut the repository into the current AI ERP operating advisor product trunk.
- v0.x: Earlier title/image generation, RAG, vector store, module governance, and workflow iterations remain recoverable from Git history.
