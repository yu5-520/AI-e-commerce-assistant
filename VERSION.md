# Current Version

```text
16.12
```

## V16.12 Meaning

V16.12 is the approval mock-workflow removal release.

It keeps the V16.11 active import gate and fixes the next import break: `approval_service.py` no longer imports the deleted `src.workflow.mock_workflow` module.

## Fixed

```text
src/services/approval_service.py no longer imports src.workflow.mock_workflow.
Approval get_task() now reads from the current SQLite task_status projection.
If a task is not in the current V16 task_status projection, approval returns 404 instead of fabricating mock data.
src/api/main.py API_VERSION is now 16.12.
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
