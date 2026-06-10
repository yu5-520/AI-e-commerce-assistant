# 2026-06-08 Generation Configuration Controls

## Change Type
frontend-configuration / backend-generation-limits / credit-estimate

## Goal
Let users choose output range before generation instead of receiving too many titles or image plans by default. Keep the UI neutral and tool-like rather than adding a “recommended execution” block.

## Files Changed
- `frontend/index.html`
- `frontend/app.js`
- `frontend/runtime.css`
- `backend/server.py`
- `frontend/README.md`
- `backend/README.md`
- `versioning/VERSION.md`
- `versioning/CHANGELOG.md`
- `runtime/version_manifest.json`

## Behavior Changed
- Frontend now includes generation configuration controls.
- User can choose `membership`, `title_count`, `image_plan_count`, and `image_generate_count`.
- Free users can choose title counts 3/5 and image plan counts 1/2.
- VIP users can choose title counts 10/15 and image plan counts 3/5.
- Image generation count is translated into credit estimate only; no real image generation is connected yet.
- Backend enforces applied counts and records requested/applied configuration.
- Frontend renders selected-count results and image credit estimates.

## Product Rule
No “recommended execution” block was added. The product flow is:

```text
User selects output range
↓
AI generates selectable schemes
↓
User copies or marks actual usage
↓
Feedback is stored for later private optimization
```

## Files Preserved
- `.github/workflows/pdd-operation-analysis.yml`
- `scripts/pdd_operation_analyzer.py`
- `scripts/llm_client.py`
- `runtime/module_chain.json`
- `runtime/rag_chain.json`
- `runtime/vector_retrieval_chain.json`
- `config/model_providers.json`

## Current Boundary
Free/VIP is currently request-level configuration, not authenticated entitlement. Real billing, credit deduction, image generation, user identity, and VIP account isolation are not connected yet.
