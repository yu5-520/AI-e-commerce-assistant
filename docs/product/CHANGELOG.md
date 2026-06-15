# Product Changelog

## v1.0.1 - 2026-06-15

### Product Decision
- The active product trunk no longer carries the old Material Observer Agent layer.
- The product script chain now treats version governance as a required CI gate before runtime and API smoke tests.
- The current product path remains the AI ERP operating-unit workbench: `src.api.main:app` → `/api/business/*` → `web_demo/app-v2.js`.

### Changed
- GitHub Actions now validates the current trunk with `scripts/check_version_governance.py`, `scripts/smoke_test_runtime.py`, and `scripts/smoke_test_api.py`.
- API version is aligned to `v1.0.1` for this script-chain repair.

### Removed From Active Product Trunk
- Removed the old Material Observer Agent files and runtime registry.
- Historical agent work remains recoverable from Git history, but it is no longer part of the active product surface.

### Product Boundary
- Future product-structure changes must update product changelog and versioning changelog together.
- CI must fail when current version, FastAPI app version, and version logs are not aligned.

## v1.0.0 - 2026-06-15

### Product Decision
- The active product trunk is now the AI ERP operating-unit workbench, not the earlier title/image generation or material-observation demo flow.
- The current user-facing path is `web_demo/index.html` + `web_demo/app-v2.js`, backed by `/api/business/*`.
- The product story is now centered on ERP-inferred operating units, cycle frequency, product health, competitor opportunities, listing suggestions, traffic review, confirmation actions, and business reports.

### Changed
- Main branch now keeps one current runnable product path.
- README and versioning records now describe the current AI ERP operating-unit product architecture.
- API surface is narrowed to the product-facing business routes plus health, data import, approval, and system maintenance routes.
- API version is aligned to `v1.0.0` as the first cleaned product trunk version.

### Removed From Active Product Trunk
- Old frontend template: `web_demo/app.js`.
- Legacy compatibility route families: `/api/demo`, `/api/products`, `/api/customers`, `/api/diagnosis`, `/api/tasks`, `/api/reports`, `/api/evals`, and `/api/logs`.
- Old standalone helpers: `src/run_demo.py`, `src/services/workflow_service.py`, `src/services/eval_service.py`, and `evals/run_evals.py`.

### Product Boundary
- The product still uses Mock ERP / CRM data.
- The product does not connect to real shop backends.
- The product does not automatically change prices, publish listings, launch ad campaigns, message customers, or process refunds.
- High-risk actions remain confirmation records only.

### Follow-up
- Future product updates that change page structure, active route families, workflow stages, or product positioning must update this file and `versioning/CHANGELOG.md` together.
