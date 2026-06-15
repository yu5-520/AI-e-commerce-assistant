# Changelog

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
- These documents described future multi-page product structure or broad domain models that could pull the current MVP back toward removed routes and old UI assumptions.

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
- Removed legacy Material Observer Agent files from the active product trunk.
- The old v0.9.x material-observation Agent remains recoverable from Git history, but it is no longer part of the current v1.x ERP operating-unit product path.

### Product Engineering Rule
- CI must run the version governance check before smoke tests.
- GitHub Actions must not reference deleted legacy entrypoints such as `src/run_demo.py`, `evals/run_evals.py`, or old local server services.
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
- Removed the old frontend template `web_demo/app.js`.
- Removed legacy compatibility routes and old helper entrypoints that pulled the project back toward the previous demo shape.

### Added
- Added `.gitignore` rules for runtime outputs, local logs, local databases, virtual environments, and environment files.

### Product Engineering Rule
- The main branch should contain only the current runnable product path.
- Old demo templates, legacy compatibility APIs, and deprecated run commands should live in Git history, not in the active product trunk.
- Every architecture-level cleanup must update this `versioning/` record and the relevant product log under `docs/product/`.

## Earlier History

- v0.9.2: Agent module governance was added with stable contract, source policy, confidence, risk flags, and runtime registry.
- v0.9.1: Material observation was moved back into an implicit backend pipeline so users only see generation progress and final outputs.
- v0.9.0: Pre-generation material sampling UI was added.
- v0.8.9: Light material observation Agent layer was added.
