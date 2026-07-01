# Current Version

```text
16.7
```

## V16.7 Meaning

V16.7 is the MVP legacy route purge release.

It keeps the V16.5 Station Alignment runtime and the V16.6 file manifest, then removes the first wave of old route pollution from the active repository.

## Changed

```text
FastAPI main.py now imports and mounts only V16 MVP runtime routes.
V9/V10/V12/V13/V14 legacy compatibility route files were deleted.
station_registry_service removed LEGACY_STATION_ALIASES.
config/v16_mvp_file_manifest.json now records purged files and removed aliases.
```

## Purged route files

```text
src/api/routes/deprecated_stations.py
src/api/routes/v9_readiness.py
src/api/routes/v10_product.py
src/api/routes/architecture.py
src/api/routes/data_source_compat.py
src/api/routes/station_handoffs.py
src/api/routes/report_task_sync.py
src/api/routes/trends.py
```

## Removed old station aliases

```text
import_station
report_parse_station
metric_fact_station
operating_object_station
operating_snapshot_station
system_product_snapshot_station
product_signal_snapshot_station
task_signal_station
rag_context_station
agent_judgment_station
task_snapshot_station
task_pool_station
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

Git history is the history archive. The current working tree only serves the MVP. Old version routes and old station aliases cannot enter the active runtime.
