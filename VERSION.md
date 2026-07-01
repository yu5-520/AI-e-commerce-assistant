# Current Version

```text
16.14
```

## V16.14 Meaning

V16.14 is the audit route context cleanup release.

It keeps the V16.13 FastAPI entrypoint repair and fixes the next active import break: `src/api/routes/audit.py` no longer imports the deleted `src.core.context` module or old trace/tech-log service fragments.

## Fixed

```text
src/api/routes/audit.py no longer imports src.core.context.
src/api/routes/audit.py no longer imports deleted trace_audit_service / tech_log_service fragments.
Audit endpoints now expose a lightweight V16-safe projection without legacy context fallback.
src/api/main.py API_VERSION is now 16.14.
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
