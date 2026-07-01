# Current Version

```text
16.10
```

## V16.10 Meaning

V16.10 is the final unmarked-file purge release.

It keeps the V16 MVP runtime and deletes the last broad group of unmarked legacy files: old schemas, old consistency scripts, old source subpackages, and old versioned service fragments.

## Current verification entry

```bash
python scripts/check_v16_manifest.py
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

Git history is the archive. The current working tree only serves the MVP. Remaining non-V16 artifacts must be explicitly promoted into the V16 manifest before they can stay.
