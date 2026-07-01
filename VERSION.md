# Current Version

```text
16.13
```

## V16.13 Meaning

V16.13 is the FastAPI entrypoint syntax repair release.

It keeps the V16.12 approval mock-workflow removal and fixes the syntax residue left in `src/api/main.py`.

## Fixed

```text
src/api/main.py no longer contains the stray string `.replace(...)` residue.
src/api/main.py now mounts frontend_views.router directly.
src/api/main.py API_VERSION is now 16.13.
```

## Current verification entry

```bash
python scripts/check_v16_manifest.py
```

The checker runs:

```python
from src.api.main import app, STATION_MAINLINE
```

## Current V16 mainline

```text
report_receive_station
-> report_schema_station
-> report_fact_station
-> product_master_station
-> product_metric_snapshot_station
-> full_product_bundle_station
-> bundle_validation_station
-> product_judgment_agent_station
-> product_judgment_package_station
-> rag_permission_context_station
-> task_mapping_agent_station
-> task_pool_admission_station
-> frontend_read_model_station
-> task_pool_acceptance_station
```

## Rule

Git history is the archive. The current working tree only serves the MVP. Active FastAPI import must pass before deleting more unmarked source files.
