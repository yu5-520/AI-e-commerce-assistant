# Changelog

## v0.3.0 - 2026-06-08

### Added
- Added version governance directory: `versioning/`.
- Added AI change rules, module ownership, change request template, and update logs.
- Added runtime version manifest for quick AI/context lookup.

### Preserved
- Existing GitHub Issue -> Actions -> DeepSeek -> Issue comment workflow remains unchanged.
- Existing `runtime/module_chain.json` remains the active runtime chain.
- Existing `docs/` files remain as compatibility/history files.

### Risk
- Version governance is documentation-enforced first; future automation can validate changelog and scope rules.

## v0.2.0 - 2026-06-08

### Added
- Added `runtime/module_chain.json`.
- Added modular folders for platform, operation modes, interface, frontend, and backend.

### Changed
- `scripts/pdd_operation_analyzer.py` now reads runtime module chain instead of hardcoded docs paths.

## v0.1.0 - 2026-06-08

### Added
- GitHub Issue templates.
- GitHub Actions workflow.
- DeepSeek/OpenAI-compatible LLM interface.
- Issue comment output loop.
