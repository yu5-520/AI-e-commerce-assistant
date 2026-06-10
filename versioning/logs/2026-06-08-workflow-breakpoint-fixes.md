# v0.8.4 Workflow Breakpoint Fixes

## Change Type
workflow-breakpoint-fix / runtime-smoke-test / issue-workflow-alignment / llm-provider-config

## Goal
Reduce workflow breakpoints between the GitHub Issue workflow, the frontend/backend generation configuration, and the model provider interface.

## Files Changed
- `.github/workflows/runtime-smoke-test.yml`
- `scripts/smoke_test_runtime.py`
- `scripts/pdd_operation_analyzer.py`
- `config/model_providers.json`
- `modules/operation_modes/natural-flow/output-template.md`
- `modules/operation_modes/paid-growth/output-template.md`
- `modules/operation_modes/hot-product/output-template.md`
- `versioning/VERSION.md`
- `versioning/CHANGELOG.md`
- `runtime/version_manifest.json`

## Fixed Breakpoints

### 1. Model Provider Path
DeepSeek provider now uses an OpenAI-compatible `/v1` base URL so `llm_client.py` can build `/chat/completions` correctly.

### 2. Runtime Guard
A separate smoke workflow was added to check Python syntax and deterministic backend generation without touching external model secrets.

### 3. Issue Workflow Configuration
The Issue analyzer now parses generation settings from Issue title/body/comments:
- title count
- image plan count
- image generation count
- free/VIP mode

If the user does not specify settings, it defaults to free-mode output.

### 4. Template Quantity Conflict
Operation mode templates now say “follow generation configuration” instead of hard-coding fixed output quantities.

## Preserved
- Existing Issue comment workflow remains active.
- Existing frontend/backend API paths remain unchanged.
- Existing responsive layout from v0.8.3 remains unchanged.
- Existing productized result schema remains unchanged.

## Remaining Risk
- The smoke test does not call external model APIs.
- Real server deployment still needs a pull/restart step before production testing.
