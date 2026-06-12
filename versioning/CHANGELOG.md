# Changelog

## v0.9.1 - 2026-06-11

### Changed
- Moved material observation back into an implicit backend/product-engineering pipeline.
- Removed user-facing material sampler and material observation cards from the normal page flow.
- Kept the optional material reference input, renamed it to “补充参考素材（可选）”.
- Added `frontend/implicit-material-pipeline.js` to show user-facing progress: 正在整理商品素材 → 正在生成可测试方案.
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
