# 2026-06-08 Feedback Knowledge Base

## Change Type
feedback / knowledge-base / template-backflow

## Goal
Add structural modules for template backflow, user feedback, operation-effect validation, and reusable knowledge storage.

## Files Added
- `modules/knowledge_base/README.md`
- `modules/knowledge_base/title_patterns.md`
- `modules/knowledge_base/image_patterns.md`
- `modules/knowledge_base/sku_patterns.md`
- `modules/knowledge_base/price_patterns.md`
- `modules/knowledge_base/operation_cases.md`
- `modules/knowledge_base/feedback_levels.md`
- `modules/feedback/feedback_schema.md`
- `modules/feedback/feedback_flow.md`
- `modules/feedback/usage_metrics.md`
- `modules/feedback/effectiveness_metrics.md`
- `runtime/feedback_chain.json`
- `runtime/knowledge_retrieval_chain.json`
- `modules/frontend/feedback-ui-schema.md`
- `modules/backend/feedback-api-contract.md`
- `modules/backend/knowledge-storage-plan.md`
- `data/feedback_samples/README.md`
- `data/knowledge_samples/README.md`

## Files Changed
- `versioning/VERSION.md`
- `versioning/CHANGELOG.md`
- `runtime/version_manifest.json`

## Files Preserved
- `.github/workflows/pdd-operation-analysis.yml`
- `scripts/pdd_operation_analyzer.py`
- `scripts/llm_client.py`
- `runtime/module_chain.json`
- `config/model_providers.json`

## Impact
No runtime generation behavior changed. Feedback and knowledge-base modules are structural definitions only and are not yet connected to the active generation script.

## Next Step
Later connect feedback collection to frontend UI and backend API, then use knowledge retrieval as optional context before LLM generation.
