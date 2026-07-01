Current Version: 16.11

V16.11 Active Import Gate

Core chain:

`report_receive_station -> report_schema_station -> report_fact_station -> product_master_station -> product_metric_snapshot_station -> full_product_bundle_station -> bundle_validation_station -> product_judgment_agent_station -> product_judgment_package_station -> rag_permission_context_station -> task_mapping_agent_station -> task_pool_admission_station -> frontend_read_model_station -> task_pool_acceptance_station`

Key fix:

- `src/api/routes/accounts.py` no longer imports the old `src.core.context` module.
- Account route user identity now uses `src.services.account_service.user_id_from_headers`.
- `src/api/main.py` now reports `API_VERSION = 16.11` and `mode = v1611_active_import_gate`.
- `scripts/check_v16_manifest.py` now runs a FastAPI active import gate.

Boundary:

V16.11 is an import-chain guardrail. More file cleanup should happen only after the active import gate passes.
