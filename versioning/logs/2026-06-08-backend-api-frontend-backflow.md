# 2026-06-08 Backend API and Frontend Backflow

## Change Type
backend-api / frontend-runtime / result-backflow / feedback-backflow

## Goal
Connect the frontend UI buttons to a local backend API so product input can generate AI operation results, return results to the frontend, and write local result/feedback backflow records.

## Files Added
- `backend/server.py`
- `backend/README.md`
- `frontend/runtime.css`
- `data/runtime_results/README.md`
- `data/runtime_feedback/README.md`

## Files Changed
- `frontend/app.js`
- `frontend/index.html`
- `frontend/README.md`
- `versioning/VERSION.md`
- `versioning/CHANGELOG.md`
- `runtime/version_manifest.json`

## Runtime Flow
1. Frontend user selects operation mode.
2. Frontend user inputs product, detail, cost, price, and stock.
3. Frontend calls `POST /api/generate`.
4. Backend reads runtime module context and calls LLM when enabled.
5. If LLM is unavailable, backend returns deterministic fallback output.
6. Backend stores the generated result under `data/runtime_results/`.
7. Frontend displays returned titles, image direction, SKU, price, and operation result.
8. User clicks feedback buttons.
9. Frontend calls `POST /api/feedback`.
10. Backend stores feedback under `data/runtime_feedback/`.

## Files Preserved
- `.github/workflows/pdd-operation-analysis.yml`
- `scripts/pdd_operation_analyzer.py`
- `scripts/llm_client.py`
- `runtime/module_chain.json`
- `runtime/rag_chain.json`
- `runtime/vector_retrieval_chain.json`
- `config/model_providers.json`

## Impact
The frontend now has a working local backend loop. The existing GitHub Issue -> Actions -> DeepSeek -> Issue comment workflow remains preserved and unchanged.

## Current Boundary
This is local MVP storage. It does not yet provide authentication, production database, object storage, VIP user isolation, payment, or permission management.

## Next Step
Connect VIP product tracking to user-specific storage and introduce persistent product profiles before production deployment.
