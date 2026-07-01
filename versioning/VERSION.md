Current Version: 16.8

V16.8 MVP Purge

Core chain:

`report_receive_station -> report_schema_station -> report_fact_station -> product_master_station -> product_metric_snapshot_station -> full_product_bundle_station -> bundle_validation_station -> product_judgment_agent_station -> product_judgment_package_station -> rag_permission_context_station -> task_mapping_agent_station -> task_pool_admission_station -> frontend_read_model_station -> task_pool_acceptance_station`

Key fix:

- Remaining legacy docs, examples, evals, old frontend, old workflows, sample data, old modules, old deploy docs, old Alembic migration artifacts, and old knowledge-base samples were removed from the active working tree.
- Git history remains the archive.
- Current repository files now serve the V16 MVP runtime.

Boundary:

V16.8 purges large legacy directories. If a removed artifact is needed later, recover it from Git history and explicitly promote it into the V16 manifest.
