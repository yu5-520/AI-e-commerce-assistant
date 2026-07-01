# Current Version

```text
16.11
```

## V16.11 Meaning

V16.11 is the active import gate release.

It keeps the V16.10 cleaned MVP repository, fixes the first active import break caused by the old source-core cleanup, and upgrades the V16 manifest checker so it runs a full FastAPI import before more source changes.

## Fixed

```text
src/api/routes/accounts.py no longer imports src.core.context.
src/api/routes/accounts.py now uses src.services.account_service.user_id_from_headers.
src/api/main.py API_VERSION is now 16.11.
scripts/check_v16_manifest.py now includes an ACTIVE IMPORT GATE.
```

## Current verification entry

```bash
python scripts/check_v16_manifest.py
```

The checker now runs:

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

Git history is the archive. The current working tree only serves the MVP. Active FastAPI import must pass before more source cleanup.
