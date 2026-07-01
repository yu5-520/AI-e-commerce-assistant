# MVP V16 File Manifest

Current marker baseline: **V16.6 MVP file marking / V16.5 Station Alignment runtime**.

This file is the human-readable V16 whitelist. The machine-readable source is:

```text
config/v16_mvp_file_manifest.json
```

## Why this exists

The repository is now a one-person MVP working repository, not a long-term enterprise version archive. Git history already keeps historical evidence. The current working tree should only serve the current MVP.

## Marker rules

```text
V16_KEEP      Current MVP mainline files.
V16_SUPPORT   Runtime support required by current MVP files.
V16_FRONTEND  Current web demo entry and modules.
V16_DOC       Current documentation only.
V16_TOOL      Current repository governance scripts.
UNMARKED      Deletion candidate after import check.
```

## V16 current mainline

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

## V16_KEEP files

```text
src/api/main.py
src/api/routes/stations.py
src/api/routes/frontend_views.py
src/api/routes/data_import.py
src/api/routes/import_jobs.py
src/api/routes/task_lifecycle_stations.py
src/api/routes/task_pool.py
src/api/routes/task_persistence.py
src/api/routes/task_snapshots.py
src/services/station_alignment_v165_service.py
src/services/station_registry_service.py
src/services/station_contract_service.py
src/services/station_adapter_service.py
src/services/station_queue_service.py
src/services/station_queue_worker_service.py
src/services/pipeline_gate_service.py
src/services/task_generation_run_service.py
src/services/module_projection_service.py
src/services/metric_catalog_service.py
src/services/system_product_snapshot_service.py
src/services/product_signal_snapshot_service.py
src/services/product_signal_snapshot_v164_service.py
src/services/signal_pool_service.py
src/services/import_adapter_service.py
src/services/import_row_store_service.py
src/services/report_profile_agent_service.py
src/services/real_product_judgment_agent_v161_service.py
src/services/real_task_mapping_agent_v162_service.py
src/services/dual_agent_product_task_service.py
src/services/agent_budget_ledger_service.py
src/services/rag_context_station_service.py
src/services/task_pool_station_service.py
src/services/task_pool_acceptance_v163_service.py
src/services/frontend_read_model_service.py
src/services/task_acceptance_assignment_station_service.py
src/services/task_submission_review_station_service.py
src/services/task_recap_rag_station_service.py
```

## V16_SUPPORT files

```text
src/repositories/sqlite_repository.py
src/services/system_service.py
src/services/account_service.py
src/services/backend_isolation_service.py
src/services/permission_stamp_service.py
src/api/routes/system.py
src/api/routes/health.py
src/api/routes/accounts.py
src/api/routes/approvals.py
src/api/routes/audit.py
src/api/routes/ops.py
src/api/routes/worker_jobs.py
requirements.txt
scripts/deploy_fast.sh
scripts/deploy_atomic.sh
```

## V16_FRONTEND

```text
web_demo/
```

## V16_DOC

```text
README.md
VERSION.md
versioning/VERSION.md
MVP_V16_FILE_MANIFEST.md
config/v16_mvp_file_manifest.json
```

## First purge candidates

These are not deleted in this marker step. They should be removed after import checks and main.py route cleanup.

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

## Legacy aliases to remove next

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

## Rule

```text
If a file is not V16_KEEP, V16_SUPPORT, V16_FRONTEND, V16_DOC, or V16_TOOL, it must be treated as a deletion candidate for the MVP repository cleanup.
```
