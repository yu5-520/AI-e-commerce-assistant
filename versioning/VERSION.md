Current Version: 16.9

V16.9 Stale Verifier Purge

Core chain:

`report_receive_station -> report_schema_station -> report_fact_station -> product_master_station -> product_metric_snapshot_station -> full_product_bundle_station -> bundle_validation_station -> product_judgment_agent_station -> product_judgment_package_station -> rag_permission_context_station -> task_mapping_agent_station -> task_pool_admission_station -> frontend_read_model_station -> task_pool_acceptance_station`

Key fix:

- Deleted `scripts/verify_release.py`.
- Deleted `scripts/check_repo_hygiene.py`.
- Removed V12/V12.9 checker pollution from the active V16 repository.
- Current verification entry is `python scripts/check_v16_manifest.py`.

Boundary:

V16.9 deletes stale check scripts only. If stronger V16 runtime verification is needed later, create a new V16-native verifier instead of restoring old V12 checkers.
