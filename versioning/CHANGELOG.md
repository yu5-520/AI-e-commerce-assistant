# Changelog

## v1.0.20 - 2026-06-15

### Changed
- Repositioned the 流量 page as `流量测试台` instead of an abstract traffic conclusion panel.
- Added `web_demo/traffic-manager-hotfix.js` with product-level traffic tests bound to image placeholder, product title, platform, shop, product link, channel, test source, and action state.
- Added `web_demo/traffic-center.css` for traffic test cards, filter menus, metric strips, backflow blocks, detail pages, and responsive layout.
- Traffic rows now show exposure, click-through rate, conversion, ROI, refund rate, inventory, status, backflow destination, and next action.
- Added interactive filters for platform, store, traffic channel, and status, plus search across product title, ID, shop, channel, status, backflow, and next action.
- Added actions for `详情`, `继续观察`, `加入任务清单`, and source jumps to 商品 / 上新 pages.
- `web_demo/index.html` now appends `?v=1.0.20` to assets and loads the traffic test workspace script.
- Aligned the FastAPI app version and health version with the repository version: `1.0.20`.

### Product Engineering Rule
- Traffic judgments must be product-level. A traffic row without product title, platform, shop, and link is incomplete.
- Traffic pages should show measurable signals: exposure, CTR, conversion, ROI, refund rate, and inventory承接.
- Backflow should be a concise field such as 售后归因、经营判断、库存承接, not a long process paragraph on the list page.
- Traffic execution remains confirmation-first; the page should not imply automatic ad spend or campaign changes.

## v1.0.19 - 2026-06-15

### Changed
- Repositioned the 上新 page as `上新测试台` instead of a single candidate-generation report.
- Added `web_demo/listing-manager-hotfix.js` with two launch-test flows: `已有商品测试` and `竞品机会测试`.
- Added `web_demo/listing-center.css` for launch test tabs, test cards, metric strips, confirmation actions, and detail pages.
- Existing-product tests now cover title tests, main-image tests, SKU tests, platform coupon/activity tests, and promotion tests.
- Competitor-opportunity tests now turn competitor gaps into launch experiments, such as installation images, dimension references, structure stability, material explanation, and support proof.
- Test cards now include source, platform, store, test type, test plan, cycle, target metric, status, risk, and actions.
- Added actions for `详情`, `确认测试`, `加入任务清单`, and source jumps to 商品 / 竞品 / 流量 pages.
- `web_demo/index.html` now appends `?v=1.0.19` to assets and loads the listing test workspace script.
- Aligned the FastAPI app version and health version with the repository version: `1.0.19`.

### Product Engineering Rule
- 上新 should mean controlled launch testing, not only new product generation.
- Existing products can be re-launched for title, main image, SKU, platform campaign, coupon, and promotion tests.
- Competitor opportunities should flow into launch experiments only after being turned into clear test actions and metrics.
- Test execution remains confirmation-first; the page should not imply automatic real shop publishing.

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

## Earlier History

- v1.0.15: Productized the 商品 page from oversized diagnosis cards into a compact goods-operation list.
- v1.0.14: Report pages support real export and template download.
- v1.0.13: Report center added user-driven report import.
- v1.0.11: Data page was renamed and productized into `ERP / CRM 报表管理`.
- v1.0.10: Operating unit page was productized into a store-group management surface.
- v1.0.9: Added dashboard cache hotfix and compatibility CSS.
- v1.0.8: Compact dashboard task board was added.
- v1.0.7: Homepage overview was repositioned as a task board.
- v1.0.0-v1.0.6: Product trunk cleanup, API alignment, health/version repair, and current route governance.
