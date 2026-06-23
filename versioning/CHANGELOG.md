# Changelog

## v9.2.0 - 2026-06-24

### Added
- Added `docs/V9_BACKEND_FLOW_CONSISTENCY.md` for V9.2 backend main-flow governance.
- Added `src/services/v92_backend_flow_service.py` to expose the backend-flow contract.
- Added `GET /api/architecture/v9/backend-flow` through `src/api/routes/architecture.py`.
- Added `scripts/check_backend_flow_consistency.py` and wired it into GitHub Actions.

### Changed
- FastAPI runtime is bumped to `9.2.0` through the `API_VERSION` constant.
- Health route and Agent registry versions are aligned to `9.2.0`.
- README is bumped to V9.2.0 and now references the backend flow guard and document.
- `web_demo/index.html` asset cache strings are bumped to `9.2.0`.
- Version and repository governance scripts now require the V9.2 backend flow document and check script.

### Product Engineering Rule
- V9.2 keeps `/api/modules` and `/api/accounts` as stable product entrypoints. V8 weight capabilities remain backend enhancement layers for existing modules; backend flow consistency is checked before runtime and API smoke tests.

## v9.1.0 - 2026-06-24

### Added
- Added `docs/V9_REPOSITORY_CONSISTENCY.md` for V9.1 repository structure governance.
- Added `scripts/check_repository_consistency.py` to validate required directories, required files, README entrypoints, workflow refs, frontend cache version, and forbidden legacy paths.
- Added Repository consistency check to `.github/workflows/runtime-smoke-test.yml` after version governance and before smoke tests.

### Changed
- FastAPI runtime is bumped to `9.1.0` through the `API_VERSION` constant.
- README is bumped to V9.1.0 and now references the repository consistency guard and document.
- `web_demo/index.html` asset cache strings are bumped to `9.1.0`.
- `scripts/check_version_governance.py` now treats `docs/V9_SAAS_CONSISTENCY_BASE.md` and `docs/V9_REPOSITORY_CONSISTENCY.md` as active docs and requires the new repository consistency script in workflow refs.

### Product Engineering Rule
- V9.1 does not change the business runtime flow. It makes repository structure, docs, scripts, workflow, and active entrypoints explicit before V9.2 begins backend main-flow consistency work. `/api/modules` and `/api/accounts` remain stable product entrypoints.

## v9.0.0 - 2026-06-24

### Added
- Added V9 SaaS enterprise consistency baseline as the active product trunk.
- Added `docs/V9_SAAS_CONSISTENCY_BASE.md` to define repository, frontend, backend, three-tier isolation, RAG isolation, permissions, audit, deployment, and smoke-test governance.
- Kept `/api/modules` and `/api/accounts` as stable product entrypoints for frontend modules and account scope.

### Changed
- FastAPI runtime is bumped to `9.0.0` through the `API_VERSION` constant.
- README is rewritten from the V5 PostgreSQL mirror entrypoint into the V9 SaaS enterprise baseline entrypoint.
- `scripts/check_version_governance.py` now reads `API_VERSION = "X.Y.Z"` as the primary runtime version source and still supports literal FastAPI `version="X.Y.Z"` fallback.

### Product Engineering Rule
- V9 does not add new frontend business modules and does not extend V8 algorithms. V9 consolidates V1-V8 capabilities into a SaaS enterprise foundation: repository consistency, frontend consistency, backend consistency, pricing-tier isolation, RAG isolation, permission/audit governance, deployment-mode governance, and test acceptance consistency.

## v4.5.3 - 2026-06-21

### Added
- Added `src/services/agent_llm_enrichment_service.py` for Module / Task / Feedback LLM + RAG enrichment.
- Module Agent outputs now include `retrievedCases`, `ragReferences`, `llmEnrichment`, `llmSummary`, `llmOperatorBrief`, `llmManagerReviewBrief`, `llmRiskCheck`, and `llmFallbackUsed`.
- Task generation and task playbook endpoints now wrap ActionPlan payloads with RAG cases and LLM enrichment.
- Feedback flywheel summary, cycle summary, and experience-card drafts now use LLM enrichment while keeping human review gates.
- Task-report frontend now renders a `方案补充` section when enriched briefs are available.

### Changed
- FastAPI app, health flags, Agent registry, frontend asset cache query strings, and version docs are bumped to `4.5.3`.
- `src/api/routes/modules/agents.py` routes module, task-generation, task-playbook, and cycle Agent outputs through the enrichment service.
- `src/api/routes/modules/feedback_flywheel.py` routes feedback outputs through the enrichment service.

### Product Engineering Rule
- RAG supplies reviewed experience cases; LLM refines wording and execution briefs. `problemType`, `ActionPlan`, permissions, task lifecycle, and human review remain deterministic.
