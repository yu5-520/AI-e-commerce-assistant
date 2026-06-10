# Changelog

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

### Risk
- The productized JSON schema is still MVP-level and may need stricter validation before production.

## v0.8.0 - 2026-06-08

### Added
- Added `backend/server.py` as a local zero-dependency backend API server.
- Added `backend/README.md` with API and run instructions.
- Added `data/runtime_results/README.md` for generated result backflow storage.
- Added `data/runtime_feedback/README.md` for frontend feedback backflow storage.
- Added `frontend/runtime.css` for runtime result, markdown, and feedback button styles.

### Changed
- Updated `frontend/app.js` so UI buttons call backend APIs instead of only rendering mock results.
- Updated `frontend/index.html` to load runtime styles and describe backend result return.
- Updated `frontend/README.md` to document the frontend-backend runtime flow.

### Runtime Flow
- Frontend product input calls `POST /api/generate`.
- Backend reads mode, product, detail, cost, price, and stock.
- Backend calls the configured LLM when enabled, otherwise returns deterministic fallback results.
- Backend stores generated results under `data/runtime_results/`.
- Frontend displays returned operation results.
- Frontend feedback buttons call `POST /api/feedback`.
- Backend stores feedback records under `data/runtime_feedback/`.

### Preserved
- Existing GitHub Issue -> Actions -> DeepSeek -> Issue comment workflow remains unchanged.
- Existing `scripts/pdd_operation_analyzer.py` remains unchanged in this update.
- Existing `scripts/llm_client.py` is reused but not modified.
- Existing RAG, vector, feedback, and knowledge-base structures remain unchanged.

### Risk
- This is still a local MVP backend. It does not yet include authentication, billing, VIP user isolation, production database, object storage, or permission management.

## v0.7.0 - 2026-06-08

### Added
- Added `frontend/` static UI prototype.
- Added `frontend/index.html` with cloud-console style product workspace.
- Added `frontend/styles.css` with white/dark theme variables and responsive card layout.
- Added `frontend/app.js` for theme switching, mode selection, and mock result rendering.
- Added `frontend/README.md` to document UI status and boundaries.

### Preserved
- Existing GitHub Issue -> Actions -> DeepSeek -> Issue comment workflow remains unchanged.
- Existing `scripts/pdd_operation_analyzer.py` remains unchanged in this update.
- Existing backend, RAG, vector, feedback, and knowledge-base structures remain unchanged.

### Risk
- Frontend is a static prototype only; it is not yet connected to backend API, GitHub Issue workflow, RAG, or model generation.

## v0.6.1 - 2026-06-08

### Changed
- Updated `scripts/pdd_operation_analyzer.py` so the first Issue input directly requests a full executable result package from the LLM.
- Updated all Issue templates to explain that more detailed input produces clearer output, while light input still generates a first version.
- Reframed follow-up comments such as “下一步” as refinement/continuation, not as a required second step for first output.

### Preserved
- Existing GitHub Issue -> Actions -> DeepSeek -> Issue comment workflow remains unchanged.
- Existing LLM provider configuration remains unchanged.
- Existing runtime module, RAG, vector, feedback, and knowledge-base structures remain unchanged.
