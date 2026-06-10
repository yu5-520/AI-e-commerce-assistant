# Changelog

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

### Desktop Experience
- Wider control-console workspace.
- Sticky sidebar.
- Sticky input panel.
- Larger output area for productized cards.

### Tablet Experience
- Narrower sidebar.
- Two-column input/output layout retained.
- Hero decoration reduced to preserve working space.
- Tracking cards collapse to two columns.

### Mobile Experience
- Single-column flow.
- Sidebar becomes horizontal scroll navigation.
- Mode cards become horizontal swipe cards.
- Generate button stays near the bottom for thumb operation.
- Smaller spacing and card radius to reduce visual pressure.

### Preserved
- Existing productized rendering from v0.8.1 remains active.
- Existing generation configuration from v0.8.2 remains active.
- Existing backend API paths and local backflow folders remain unchanged.

### Risk
- Responsive layout has not yet been validated against real device screenshots from production browsers.

## v0.8.2 - 2026-06-08

### Added
- Added generation configuration controls in `frontend/index.html`.
- Added free/VIP option handling in `frontend/app.js`.
- Added backend generation limit enforcement in `backend/server.py`.
- Added image generation credit estimate handling through `image_generation_plan`.

### Changed
- Frontend now sends `membership`, `title_count`, `image_plan_count`, and `image_generate_count` to `POST /api/generate`.
- Backend now generates only the selected number of title and image direction options instead of generating full output and relying on frontend trimming.
- Free users are limited to title counts 3/5, image plan counts 1/2, and image generation counts 0/1/2.
- VIP users can select title counts 10/15, image plan counts 3/5, and image generation counts 3/5.
- Result output now includes a generation configuration summary and image credit estimate when image generation is selected.

### Product Rule
- The UI does not use a “recommended execution” block. It lets users choose the generation range, receive selectable schemes, copy items, and feed back what they actually used.

### Preserved
- Existing GitHub Issue -> Actions -> DeepSeek -> Issue comment workflow remains unchanged.
- Existing backend API paths remain unchanged: `POST /api/generate`, `POST /api/feedback`, `GET /api/health`.
- Existing productized rendering cleanup from v0.8.1 remains active.

### Risk
- Image generation is still only an estimated credit plan. No real image generation model, billing, or deduction system is connected yet.

## v0.8.1 - 2026-06-08

### Changed
- Updated `backend/server.py` to return a cleaned `product_result` structure for frontend rendering.
- Updated `frontend/app.js` to render productized cards instead of exposing raw markdown as the main result.
- Updated `frontend/runtime.css` to style copyable title cards, image direction cards, SKU tables, price/action lists, and debug panels.
- Updated `frontend/README.md` and `backend/README.md` to document the productized rendering cleanup boundary.

### Product Result Fields
- `titles`: copyable title cards with tag and use case.
- `image_directions`: main text, sub text, visual structure, and use case.
- `sku_plans`: SKU type, example, and purpose.
- `price_advice`: direct price actions.
- `activity_suggestions`: activity or paid-growth suggestions.
- `next_actions`: operational next steps.
- `precision_tips`: optional fields that improve the next generation.

### Product Cleanup Rules
- Main frontend result does not expose `result_id`, `llm_status`, `backflow_status`, fallback state, API names, or other engineering fields.
- Engineering fields are available only inside the developer debug panel.
- Copy/use feedback is attached to the exact item text where possible.

### Preserved
- Existing GitHub Issue -> Actions -> DeepSeek -> Issue comment workflow remains unchanged.
- Existing backend API paths remain unchanged: `POST /api/generate`, `POST /api/feedback`, `GET /api/health`.
- Existing local backflow folders remain unchanged.
