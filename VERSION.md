# Current Version

```text
16.6
```

## V16.6 Meaning

V16.6 is the MVP file marking release.

It keeps the V16.5 Station Alignment runtime and adds a V16 manifest layer so the repository can be cleaned for MVP use.

## Manifest

```text
MVP_V16_FILE_MANIFEST.md
config/v16_mvp_file_manifest.json
scripts/check_v16_manifest.py
```

## Marker rules

```text
V16_KEEP      Current MVP mainline files.
V16_SUPPORT   Runtime support required by current MVP files.
V16_FRONTEND  Current web demo entry and modules.
V16_DOC       Current documentation only.
V16_TOOL      Current repository governance scripts.
UNMARKED      Deletion candidate after import check.
```

## Mainline remains V16.5 runtime

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

Git history is the history archive. The current working tree only serves the MVP. Files outside the V16 manifest are deletion candidates after import checks and route cleanup.
