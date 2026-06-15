# Changelog

## v1.0.0 - 2026-06-15

### Changed
- Recut the repository into a single current product trunk: `src.api.main:app` → `/api/business/*` → `web_demo/app-v2.js`.
- Updated `src/api/main.py` so it only mounts the current product-facing API surface plus health, data import, approval, and system maintenance routes.
- Aligned the FastAPI app version with the version governance record: `version="1.0.0"`.
- Updated `scripts/start_server.sh` to default to `127.0.0.1:3000`, keeping public access behind Nginx.
- Rewrote `README.md` around the current AI ERP operating-unit product architecture and deployment path.
- Updated `scripts/smoke_test_api.py` so API smoke tests verify only current product routes.
- Added `docs/product/CHANGELOG.md` as the product-level log for positioning, page/API boundary, and active trunk changes.

### Removed
- Removed the old frontend template `web_demo/app.js`.
- Removed legacy compatibility routes: `/api/demo`, `/api/products`, `/api/customers`, `/api/diagnosis`, `/api/tasks`, `/api/reports`, `/api/evals`, and `/api/logs`.
- Removed old helper entrypoints and services that pulled the project back toward the previous demo shape: `src/run_demo.py`, `src/services/workflow_service.py`, `src/services/eval_service.py`, and `evals/run_evals.py`.

### Added
- Added `.gitignore` rules for runtime outputs, local logs, local databases, virtual environments, and environment files.

### Product Engineering Rule
- The main branch should contain only the current runnable product path.
- Old demo templates, legacy compatibility APIs, and deprecated run commands should live in Git history, not in the active product trunk.
- Every architecture-level cleanup must update this `versioning/` record and the relevant product log under `docs/product/`.

### Risk / Follow-up
- Server instances must run `git pull origin main` and redeploy before the online page reflects this cleanup.
- Any docs or tests that still reference removed legacy routes should be treated as stale and updated or deleted.

## v0.9.2 - 2026-06-11

### Added
- Added Agent module governance for the material observation layer.
- `scripts/material_observer.py` now exposes a stable Agent contract through `agent_contract()`.
- Material observation output now includes `agent_id`, `agent_version`, `stage`, `source_policy`, `risk_flags`, `confidence`, and `agent_trace`.
- Added `runtime/agent_registry.json` so current and future Agents can be registered and governed in one place.
- Runtime smoke test now validates the Agent contract, source policy, risk flags, confidence output, and stale-year filtering.

### Product Engineering Rule
- Agent outputs are product-engineering records, not normal user-facing UI.
- Agents must expose a stable contract before being used by generation flows.
- Agents must declare allowed and disallowed data sources.
- Material observation can use user-provided text, merchant-owned data, uploaded screenshot text, and legal search APIs.
- Material observation must not use unauthorized platform scraping or copy competitor titles verbatim.

### Preserved
- v0.9.1 implicit user flow remains active.
- v0.8.8 title stale-year filtering remains active.
- v0.8.7 anonymous page memory remains active.

## v0.9.1 - 2026-06-11

### Changed
- Moved material observation back into an implicit backend/product-engineering pipeline.
- Removed user-facing material sampler and material observation cards from the normal page flow.
- Kept the optional material reference input, renamed it to “补充参考素材（可选）”.
- Updated the main frontend generation flow in `frontend/app.js` to show user-facing progress: 正在整理商品素材 → 正在生成可测试方案.
- Final output remains focused on copyable titles, image directions, SKU plans, price advice, and next actions.

### Product Experience Rule
- Users should click once and receive final usable outputs.
- Material observation is a product-engineering capability, not a user confirmation step.
- The page should not expose internal material packs, search tasks, or Agent observation details to normal users.

### Preserved
- Backend material observation Agent from v0.8.9 remains active.
- Title stale-year filtering from v0.8.8 remains active.
- Anonymous page memory from v0.8.7 remains active.

### Risk
- Material observation is still saved in backend result records for engineering review, but it is no longer visible in the normal user interface.

## v0.9.0 - 2026-06-11

### Added
- Added a pre-generation “观察素材” button next to the material reference input.
- Added `frontend/material-sampler.js` and `frontend/material-sampler.css`.
- Users can now preview wording signals, title structures, and sampling suggestions before generating a full product plan.
- The sampler uses the same product/mode/material context as the generation flow, preparing the UI for a future backend search/API sampling source.

### Product Experience Rule
- Users should be able to inspect market wording signals before committing to generation.
- Material sampling is a step before generation, not hidden only inside the final result.
- This remains a compliant light sampler: it does not scrape platform pages.

### Preserved
- Existing material observation Agent output from v0.8.9 remains active.
- Existing title stale-year filtering from v0.8.8 remains active.
- Existing anonymous page memory from v0.8.7 remains active.

### Risk
- This version is frontend-side pre-sampling only; it does not yet call a dedicated backend `/api/material-observe` endpoint.
- Future versions should connect this UI to legal search APIs, uploaded screenshots, or merchant-owned data sources.

## v0.8.9 - 2026-06-11

### Added
- Added the light version of a material observation Agent layer in `scripts/material_observer.py`.
- The backend now builds a material pack from user-provided competitor titles, main-image selling points, or platform phrases.
- The material observation Agent outputs search tasks, usable terms, title structures, banned terms, and next sampling suggestions.
- The generation prompt now receives the material observation pack together with the current time and season context.
- The model is instructed to extract wording structure and current phrase feel, not to copy competitor titles directly.
