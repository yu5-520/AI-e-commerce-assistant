# Changelog

## v1.0.5 - 2026-06-15

### Fixed
- Repaired the backend API contract for approval status roundtrip.
- `/api/business/actions` now merges persisted approval status from the approval service before returning product-facing action cards.
- `/api/health` now returns the current API version and product name instead of a generic text label.
- Added `/api/system/clear-runtime-data` as the current system cleanup endpoint while keeping `/api/system/clear-demo-data` as a backward-compatible alias.
- Strengthened `scripts/smoke_test_api.py` so CI verifies approve/reject state is visible again through `/api/business/actions`.
- Aligned the FastAPI app version with the repository version: `version="1.0.5"`.

### Product Engineering Rule
- Approval state must be visible through product-facing business APIs, not only through low-level approval endpoints.
- Health output must reflect the current application version.
- New endpoint names should use current product terminology; legacy names may remain only as compatibility aliases.

## v1.0.4 - 2026-06-15

### Changed
- Aligned the frontend UI with the productized `/api/business/*` API surface.
- `web_demo/app-v2.js` now uses dedicated product endpoints for product health, competitor opportunities, listing suggestions, traffic review, action confirmations, and business reports.
- `web_demo/index.html` now uses clearer business hash sections such as `#business-products`, `#business-traffic`, and `#business-report`.
- Removed the unused import action from the frontend runtime.
- Added a Chinese label for `passed` data-health status.
- Aligned the FastAPI app version with the repository version: `version="1.0.4"`.
- Extended `scripts/check_version_governance.py` so the removed standalone data-import stylesheet cannot return to active trunk.

### Removed
- Removed `web_demo/data-import.css` from active trunk.

### Product Engineering Rule
- Frontend pages should prefer productized `/api/business/*` endpoints instead of rendering directly from raw workflow internals.
- Removed frontend components should be blocked by version governance, not only deleted once.

## v1.0.3 - 2026-06-15

### Changed
- Removed the old module-chain memory layer from the active product trunk.
- Added `src/reports/generate_operating_report.py` and updated workflow/service imports to use the current operating report output.
- `src/workflow/mock_workflow.py` now describes itself as the FastAPI business API and smoke-test orchestration layer, not a removed CLI demo layer.
- `src/services/business_view_service.py` now reads `outputs/operating_report.md`.
- Aligned the FastAPI app version with the repository version: `version="1.0.3"`.
- Extended `scripts/check_version_governance.py` so removed module-chain roots and old report naming cannot return to active trunk.

### Removed
- Removed `runtime/module_chain.json`.
- Removed obsolete module files under the old `modules/` tree from active trunk.
- Removed `src/reports/generate_demo_report.py`.

### Product Engineering Rule
- Active module memory must come from the real runtime chain: `src.api.main:app` → `/api/business/*` → `business_view_service` → `mock_workflow` → current ERP operating-unit modules.
- Old module registries should live in Git history, not in active trunk.
- Report modules must use current product naming, not old demo naming.

## v1.0.2 - 2026-06-15

### Changed
- Cleaned the active documentation trunk so current docs describe only the v1.x ERP operating-unit product path.
- Updated README and `docs/product/README.md` to use the same product-log rules and current file map.
- Rewrote `docs/product/mvp-scope.md` around the current single-page product, `/api/business/*`, and current smoke tests.
- Rewrote `docs/product/module-boundary.md` around current API, workflow, frontend, scripts, CI, and documentation boundaries.
- Extended `scripts/check_version_governance.py` so active docs are checked for stale legacy snippets.
- Aligned the FastAPI app version with the repository version: `version="1.0.2"`.

### Removed
- Removed outdated planning documents from the active product docs: `docs/product/product-map.md`, `docs/product/user-flow.md`, and `docs/product/domain-model.md`.

### Product Engineering Rule
- Active docs must describe the current runnable trunk, not future blueprints or deleted route families.
- Future planning belongs in a new clearly marked proposal document, not in current MVP docs.
- Version governance must fail if active docs reintroduce stale commands such as old demo runs or removed route checks.

## v1.0.1 - 2026-06-15

### Fixed
- Repaired the GitHub Actions script chain so CI checks the current product trunk instead of deleted legacy entrypoints.
- `.github/workflows/runtime-smoke-test.yml` now runs syntax checks, `scripts/check_version_governance.py`, `scripts/smoke_test_runtime.py`, and `scripts/smoke_test_api.py`.
- Added `scripts/check_version_governance.py` to enforce version/log consistency before smoke tests run.
- Aligned the FastAPI app version with the repository version: `version="1.0.1"`.

### Removed
- Removed legacy Agent files from the active product trunk.
- Historical agent work remains recoverable from Git history, but it is no longer part of the current v1.x ERP operating-unit product path.

### Product Engineering Rule
- CI must run the version governance check before smoke tests.
- If a future cleanup removes routes, folders, workflows, or product entrypoints, the same change must update `versioning/VERSION.md`, `versioning/CHANGELOG.md`, and `docs/product/CHANGELOG.md`.

## v1.0.0 - 2026-06-15

### Changed
- Recut the repository into a single current product trunk: `src.api.main:app` → `/api/business/*` → `web_demo/app-v2.js`.
- Updated `src/api/main.py` so it only mounts the current product-facing API surface plus health, data import, approval, and system maintenance routes.
- Updated `scripts/start_server.sh` to default to `127.0.0.1:3000`, keeping public access behind Nginx.
- Rewrote `README.md` around the current AI ERP operating-unit product architecture and deployment path.
- Updated `scripts/smoke_test_api.py` so API smoke tests verify only current product routes.
- Added `docs/product/CHANGELOG.md` as the product-level log for positioning, page/API boundary, and active trunk changes.

### Removed
- Removed the old frontend template, legacy compatibility routes, and old helper entrypoints that pulled the project back toward the previous demo shape.

### Added
- Added `.gitignore` rules for runtime outputs, local logs, local databases, virtual environments, and environment files.

### Product Engineering Rule
- The main branch should contain only the current runnable product path.
- Old demo templates, legacy compatibility APIs, and deprecated run commands should live in Git history, not in the active product trunk.
- Every architecture-level cleanup must update this `versioning/` record and the relevant product log under `docs/product/`.

## Earlier History

- v0.9.2: Agent module governance was added.
- v0.9.1: Material observation was moved back into an implicit backend pipeline.
- v0.9.0: Pre-generation material sampling UI was added.
- v0.8.9: Light material observation Agent layer was added.
