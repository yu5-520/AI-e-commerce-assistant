# 2026-06-08 Version Governance

## Change Type
versioning / governance

## Goal
Add a governance layer so future AI edits stay scoped, traceable, and recoverable.

## Files Added
- `versioning/VERSION.md`
- `versioning/CHANGELOG.md`
- `versioning/AI_CHANGE_RULES.md`
- `versioning/MODULE_OWNERSHIP.md`
- `versioning/CHANGE_REQUEST_TEMPLATE.md`
- `runtime/version_manifest.json`
- `versioning/logs/2026-06-08-version-governance.md`

## Files Preserved
- `.github/workflows/pdd-operation-analysis.yml`
- `runtime/module_chain.json`
- `scripts/pdd_operation_analyzer.py`
- `scripts/llm_client.py`
- `modules/`
- `docs/`
- `config/model_providers.json`

## Impact
No runtime behavior changed in this update. This change only adds governance and trace files.

## Future Rule
Before broad AI edits, read `versioning/AI_CHANGE_RULES.md` and `versioning/MODULE_OWNERSHIP.md`, then update changelog or add a log file after meaningful changes.
