# Deprecated Station Archive

This directory is a storage station for old files. It is not part of the business mainline.

Rules:

- Do not import archive-only files from `src/api/main.py`.
- Do not register archive-only files in `station_registry_service.py`.
- Do not include archive-only files in frontend entry points.
- Do not call archive-only services from pipeline compatibility routes.
- Legacy services that still power real stations must stay behind `station_adapter_service.py` and be registered as adapter dependencies.

Current first-batch physical migration:

- `src/services/v112_task_chain_fix_service.py`
- `src/services/v1211_agent_sop_enhancement_service.py`
- `src/services/v1212_rag_llm_agent_service.py`

The original contents remain recoverable from Git history. Archive files here keep the governance record and replacement station mapping in the current tree.
