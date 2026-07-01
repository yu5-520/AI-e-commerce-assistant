Current Version: 16.12

V16.12 Approval Mock-Workflow Removal

Core chain:

`report_receive_station -> report_schema_station -> report_fact_station -> product_master_station -> product_metric_snapshot_station -> full_product_bundle_station -> bundle_validation_station -> product_judgment_agent_station -> product_judgment_package_station -> rag_permission_context_station -> task_mapping_agent_station -> task_pool_admission_station -> frontend_read_model_station -> task_pool_acceptance_station`

Key fix:

- `src/services/approval_service.py` no longer imports the old deleted `src.workflow.mock_workflow` module.
- Approval reads the current SQLite `task_status` projection.
- Missing current task status returns 404 instead of creating mock approval data.
- `src/api/main.py` now reports `API_VERSION = 16.12` and `mode = v1612_approval_mock_workflow_removed`.

Boundary:

V16.12 is an import-chain cleanup. More file cleanup should happen only after the active import gate passes.
