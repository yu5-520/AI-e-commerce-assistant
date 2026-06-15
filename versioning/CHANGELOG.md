# Changelog

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

## Earlier History

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
