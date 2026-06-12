# Changelog

## v0.8.9 - 2026-06-11

### Added
- Added the light version of a material observation Agent layer in `scripts/material_observer.py`.
- The backend now builds a material pack from user-provided competitor titles, main-image selling points, or platform phrases.
- The material observation Agent outputs search tasks, usable terms, title structures, banned terms, and next sampling suggestions.
- The generation prompt now receives the material observation pack together with the current time and season context.
- The model is instructed to extract wording structure and current phrase feel, not to copy competitor titles directly.
- Added frontend material observation rendering through `frontend/material-observation.js` and `frontend/material-observation.css`.
- Runtime smoke test now checks that generated results include material observation output.

### Product Experience Rule
- The product should move from static template generation toward current-market wording calibration.
- User-provided material is treated as market signal, not as copy text.
- Material observation is shown to users so they can see why the generated titles are not just template output.
- This version prepares the architecture for future search/API-based observation without scraping platforms directly.

### Preserved
- Existing title stale-year filtering from v0.8.8 remains active.
- Existing anonymous page memory from v0.8.7 remains active.
- Existing navigation reduction from v0.8.6 remains active.

### Risk
- This is still a light Agent layer. It does not yet autonomously search the web or platform pages.
- If no material reference is provided, the system uses time context, generated observation tasks, and built-in title structures.

## v0.8.8 - 2026-06-11

### Added
- Added current time and season context to web generation.
- Added optional market material input so users can paste current competitor titles, image selling points, or platform phrases.
- Added lightweight material-pack extraction that keeps recent samples and candidate terms without requiring a full manual RAG build.
- Added stale-year filtering so generated product results should not contain outdated year terms such as 2024 when the current year has moved on.
- Added smoke-test coverage for stale-year filtering and market context output.

### Product Experience Rule
- Titles should not be generated only from static templates.
- Current time, season, and user-provided material references should calibrate title wording before output.
- Reference materials are used to extract current wording structure, not to copy competitor titles directly.

### Preserved
- Existing anonymous page memory from v0.8.7 remains active.
- Existing navigation reduction from v0.8.6 remains active.
- Existing generation configuration controls remain active.

### Risk
- This is still a lightweight material layer, not a full autonomous market-observation Agent.
- If users do not provide material references and no external data source is connected, the system still relies on its built-in rules plus current time context.

## v0.8.7 - 2026-06-11

### Added
- Added anonymous browser memory through `client_id` so one browser can restore its own recent product plans after refresh.
- Added backend result listing through `GET /api/results?client_id=...`.
- Added client-aware result loading through `GET /api/results/<result_id>?client_id=...`.
- Added frontend automatic restoration of the last generated result through `localStorage`.
- Added a lightweight “最近方案” panel so users can reopen recent generated plans.

### Product Experience Rule
- Refreshing the page should not erase the last generated product plan.
- Multiple people using the same website should not share one global result screen.
- MVP memory is anonymous and browser-based; it is not yet a full account or shop login system.

### Preserved
- Existing generation configuration controls remain active.
- Existing AI generation and fallback behavior remain active.
- Existing navigation reduction from v0.8.6 remains active.

### Risk
- Memory is isolated by browser `localStorage` client ID, not by formal user login.
- Clearing browser data or changing devices will create a new anonymous history.

## v0.8.6 - 2026-06-11

### Changed
- Simplified navigation so the top bar no longer duplicates the sidebar module list.
- Top bar now acts as a light product header with brand, navigation toggle, and theme switch.
- Sidebar navigation now uses unified product names: 生成方案、商品跟进、图片积分、知识库、系统设置。
- Added collapsible sidebar behavior for desktop and drawer-style navigation for tablet/mobile.
- Main workspace gets more usable space when navigation is collapsed.

### Product Experience Rule
- Top bar identifies the product and holds lightweight controls.
- Sidebar carries product modules.
- Navigation can be hidden when the user is focused on generation and result reading.
- Tablet and mobile screens should not be permanently squeezed by two navigation layers.

### Preserved
- Existing v0.8.5 UI microcopy reduction remains active.
- Existing generation configuration controls remain active.
- Existing backend API paths remain unchanged.
- Existing responsive layout remains compatible with the new navigation shell.

### Risk
- Collapsed navigation depends on `frontend/nav.js`. If the file is not deployed with `index.html`, the navigation toggle will not work.
