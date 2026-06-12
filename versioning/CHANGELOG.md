# Changelog

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

## v0.8.5 - 2026-06-10

### Changed
- Reduced explanatory microcopy across the main frontend page.
- Simplified the hero section to focus on the user action: input a product and generate a testable operation plan.
- Removed unnecessary small text under mode cards, input panels, generation configuration, and result preview.
- Simplified runtime result sections so cards read like product output instead of system documentation.
- Replaced user-facing engineering terms such as backend, interface, debug, fallback, and backflow with simpler product language.

### Product Language Rule
- Titles carry the main meaning.
- Buttons carry the action.
- Cards carry the choice.
- Small text appears only when it prevents confusion or confirms status.

### Preserved
- Existing generation configuration controls remain active.
- Existing backend API paths remain unchanged.
- Existing responsive layout from v0.8.3 remains unchanged.
- Existing workflow breakpoint fixes from v0.8.4 remain unchanged.

### Risk
- The page is now cleaner, but some first-time users may need clearer onboarding later if they do not understand the generation options.

## v0.8.4 - 2026-06-08

### Fixed
- Fixed the DeepSeek provider default configuration by using an OpenAI-compatible `/v1` base URL and a stable `deepseek-chat` default model.
- Added `scripts/smoke_test_runtime.py` to validate that backend generation still returns the expected product result schema.
- Added `.github/workflows/runtime-smoke-test.yml` as an independent CI guard that does not touch model secrets.
- Updated the GitHub Issue analyzer so Issue body or comments can specify generation configuration such as title count, image plan count, image generation count, and VIP/free mode.
- Updated operation-mode output templates so they follow generation configuration instead of hard-coded output quantities.

### Workflow Alignment
- Web frontend generation and GitHub Issue generation now share the same product rule: output quantity should follow selected or parsed generation configuration.
- If an Issue does not specify configuration, the Issue workflow defaults to free-mode output: 3 titles, 1 image plan, and 0 image generation.
- If an Issue requests values above free limits without VIP wording, the script safely clamps the result to free limits.

### Preserved
- Existing `pdd-operation-analysis.yml` remains active for Issue comments and still uses the configured model environment.
- Existing backend API paths remain unchanged: `POST /api/generate`, `POST /api/feedback`, `GET /api/health`.
- Existing v0.8.3 responsive frontend layout remains unchanged.

### Risk
- The independent smoke test validates local deterministic generation only. It does not call external model APIs.
- The original Issue workflow was not rewritten directly because it references model secret variables; the safer fix was to add a separate non-secret CI smoke workflow.

## v0.8.3 - 2026-06-08

### Changed
- Updated `frontend/styles.css` to improve desktop, tablet, and mobile page experience.
- Desktop now keeps the left navigation and input panel sticky for long result pages.
- Tablet layout now compresses the sidebar and keeps an efficient two-column workspace.
- Mobile layout now uses a single-column flow, horizontal navigation, swipeable mode cards, and a bottom-sticky generate button.
- Form controls now include `select` styling and 16px mobile input text to avoid mobile browser zoom-in.
