Current Version: 12.14.3

V12.14.3 Deprecated Physical Archive Migration

This release performs the first physical migration of archive-only legacy files out of `src/services` and into Deprecated Station Archive.

Core rule:

- Archive-only files must not sit in the main service directory.
- Business Mainline contains only clean stations and adapter dependencies.
- Deprecated Station Archive owns old patch files and old monkey-patch records.
- Legacy services still used by Station Adapter remain in `src/services` until their station internals are extracted.

Key updates:

- Added `src/deprecated_stations/` and `src/deprecated_stations/archive_services/`.
- Archived first-batch legacy patch records:
  - `v112_task_chain_fix_service`
  - `v1211_agent_sop_enhancement_service`
  - `v1212_rag_llm_agent_service`
- Removed the original first-batch archive-only files from `src/services`.
- Updated `src/services/deprecated_station_registry_service.py` to point archive-only entries to their new physical archive paths.
- Updated `mainline_purity_check()` to fail if archive-only original paths reappear.
- Updated `src/api/main.py` to `12.14.3`.

Current contract:

Business mainline code cannot import archive-only files. The archive stores governance records and original blob references. Useful legacy logic must be migrated through explicit station adapters, not through old startup hooks or direct imports.
