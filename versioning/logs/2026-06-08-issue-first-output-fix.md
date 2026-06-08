# 2026-06-08 Issue First Output Fix

## Change Type
issue-workflow / prompt-behavior / first-output

## Goal
Fix the Issue workflow so the first Issue input directly generates a full executable result package. Users should not need to comment “下一步” just to get the first complete output.

## Problem
The previous logic treated “下一步 / 执行包 / 生成标题” as the trigger for a full execution package. This caused the first Issue output to be too much like a prompt or partial result.

## Files Changed
- `scripts/pdd_operation_analyzer.py`
- `.github/ISSUE_TEMPLATE/01-natural-flow.yml`
- `.github/ISSUE_TEMPLATE/02-paid-growth.yml`
- `.github/ISSUE_TEMPLATE/03-hot-product.yml`
- `versioning/VERSION.md`
- `versioning/CHANGELOG.md`
- `runtime/version_manifest.json`

## Behavior Changed
- First Issue input now asks the LLM to directly output a complete executable result package.
- Follow-up comments such as “下一步” are treated as refinement or continuation, not as a required second step.
- The output may still include a short “补充这些信息会更精准” section, but missing information should not block the first result.

## Files Preserved
- `.github/workflows/pdd-operation-analysis.yml`
- `scripts/llm_client.py`
- `runtime/module_chain.json`
- `runtime/rag_chain.json`
- `runtime/vector_retrieval_chain.json`
- `config/model_providers.json`

## Impact
Runtime generation behavior changed intentionally: first Issue output is now more complete. Workflow trigger and LLM provider settings were not changed.
