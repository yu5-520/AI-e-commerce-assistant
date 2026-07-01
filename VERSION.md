# Current Version

```text
16.9
```

## V16.9 Meaning

V16.9 is the stale verifier purge release.

It keeps the V16.8 MVP-purged runtime and removes old V12 release/hygiene checkers that were still enforcing V12/V12.9 rules against the V16 repository.

## Deleted

```text
scripts/verify_release.py
scripts/check_repo_hygiene.py
```

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

Git history is the history archive. The current working tree only serves the MVP. Old check scripts cannot enforce old semantic/version/route rules against the V16 MVP repository.
