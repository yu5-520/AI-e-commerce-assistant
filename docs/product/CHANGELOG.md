# Product Changelog

## v1.0.20 - 2026-06-15

### Product Decision
- The 流量 page is now a product-level traffic test workspace, not an abstract traffic conclusion page.
- Every traffic judgment must bind to a specific product with image, title, platform, shop, and product link.
- Traffic cards should show measurable signals: exposure, CTR, conversion, ROI, refund rate, inventory, status, backflow destination, and next action.
- Current product truth remains: `web_demo/index.html?v=1.0.20` → `web_demo/traffic-manager-hotfix.js?v=1.0.20` + `web_demo/traffic-center.css?v=1.0.20` → 流量测试台.

### Changed
- Added `web_demo/traffic-manager-hotfix.js` to replace the old traffic page after render.
- Added `web_demo/traffic-center.css` for product-level traffic cards, filters, metric strips, backflow blocks, and detail pages.
- The page now shows product title, image placeholder, platform, store, product link, traffic channel, test source, target, cycle, exposure, CTR, conversion, ROI, refund rate, inventory, status, and next step.
- Added filters for platform, store, traffic entrance, and status, plus search by product, shop, channel, status, backflow, and next step.
- Added `详情`, `继续观察`, `加入任务清单`, and source jump actions to 商品 / 上新 pages.
- `web_demo/index.html` now bumps frontend assets to `?v=1.0.20` and loads the traffic test workspace script.
- API version is aligned to `v1.0.20` for this product surface update.

### Product Boundary
- This is a merchant-facing UI productization patch.
- `继续观察` and `加入任务清单` are local confirmation-style interactions.
- The page does not launch real paid traffic, join platform campaigns, change budgets, or modify shop listings.
- Traffic numbers remain Mock ERP / CRM / marketplace data until real platform connectors are attached.

## v1.0.19 - 2026-06-15

### Product Decision
- The 上新 page is now a launch-test workspace, not a one-off candidate-generation page.
- 上新 has two primary flows: existing-product tests and competitor-opportunity tests.
- Existing-product tests cover title, main image, SKU, platform campaign, platform coupon, and promotion experiments.
- Competitor opportunities should be converted into testable launch versions with cycle, target metrics, and execution boundaries.
- Current product truth remains: `web_demo/index.html?v=1.0.19` → `web_demo/listing-manager-hotfix.js?v=1.0.19` + `web_demo/listing-center.css?v=1.0.19` → 上新测试台.

### Changed
- Added `web_demo/listing-manager-hotfix.js` to replace the old listing page after render.
- Added `web_demo/listing-center.css` for launch test workspace tabs, cards, metric strips, detail pages, and confirmation actions.
- The page now has two tabs: `已有商品测试` and `竞品机会测试`.
- Test cards now show source, platform, store, test type, test version, test cycle, target metric, due time, status, risk, and actions.
- Added launch-test examples for title tests, main-image tests, SKU tests, platform coupon/activity tests, promotion tests, and competitor-driven opportunity tests.
- Added `详情`, `确认测试`, `加入任务清单`, and source jump actions.
- `web_demo/index.html` now bumps frontend assets to `?v=1.0.19` and loads the listing test workspace script.
- API version is aligned to `v1.0.19` for this product surface update.

### Product Boundary
- This is a merchant-facing UI productization patch.
- `确认测试` records a local confirmation-style state; it does not publish real listings, change prices, join platform campaigns, or launch paid promotions.
- Test data remains Mock ERP / CRM / marketplace data until real platform connectors are attached.

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

## Earlier History

- v1.0.16: Product list layout was hardened for long titles.
- v1.0.15: Productized the 商品 page from oversized diagnosis cards into a compact goods-operation list.
- v1.0.14: Report pages support real export and template download.
- v1.0.11: Data page became ERP / CRM report management.
- v1.0.10: Operating unit page became store-group management.
- v1.0.9: Added dashboard cache hotfix and compatibility CSS.
- v1.0.8: Compact dashboard task board was added.
- v1.0.7: Homepage overview was repositioned as a task board.
- v1.0.0-v1.0.6: Product trunk cleanup, API alignment, health/version repair, and current route governance.
