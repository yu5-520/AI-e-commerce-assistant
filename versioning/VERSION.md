Current Version: 16.14

V16.14 Audit Route Context Cleanup

Core chain:

`report_receive_station -> report_schema_station -> report_fact_station -> product_master_station -> product_metric_snapshot_station -> full_product_bundle_station -> bundle_validation_station -> product_judgment_agent_station -> product_judgment_package_station -> rag_permission_context_station -> task_mapping_agent_station -> task_pool_admission_station -> frontend_read_model_station -> task_pool_acceptance_station`

Key fix:

- `src/api/routes/audit.py` no longer imports `src.core.context`.
- Audit endpoints now use `src.services.account_service.user_id_from_headers`.
- Audit endpoints return a lightweight V16-safe projection while MVP runtime cleanup continues.
- `src/api/main.py` now reports `API_VERSION = 16.14` and `mode = v1614_audit_context_cleanup`.

Boundary:

V16.14 is an import-chain cleanup for the audit route. More file cleanup should happen only after the active import gate passes.
