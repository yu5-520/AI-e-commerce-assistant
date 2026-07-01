Current Version: 16.7

V16.7 MVP Legacy Route Purge

Core chain:

`report_receive_station -> report_schema_station -> report_fact_station -> product_master_station -> product_metric_snapshot_station -> full_product_bundle_station -> bundle_validation_station -> product_judgment_agent_station -> product_judgment_package_station -> rag_permission_context_station -> task_mapping_agent_station -> task_pool_admission_station -> frontend_read_model_station -> task_pool_acceptance_station`

Key fix:

- FastAPI active runtime now imports only V16 MVP routes.
- V9/V10/V12/V13/V14 legacy compatibility routes were deleted.
- station_registry_service no longer accepts legacy station aliases.
- Git history remains the archive; current working tree serves the MVP.
- Remaining unmarked files should be reviewed by scripts/check_v16_manifest.py before second-wave purge.

Boundary:

V16.7 removes old runtime entry points and old station aliases. It does not delete every unmarked file yet; the second wave should be based on the manifest checker output after deployment import checks.
