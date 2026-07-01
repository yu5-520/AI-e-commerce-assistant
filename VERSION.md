# Current Version

```text
16.5
```

## V16.5 Meaning

V16.5 is the Station Alignment release.

It keeps the real report fact layer, real product judgment Agent, real RAG task mapping Agent, and current-run task-pool acceptance. The key change is that the station system is aligned again across Registry, Contract, Queue, Adapter, and Data-line.

## Mainline

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

## Rules

- One station has one responsibility, one input contract, one output artifact, and one acceptance metric.
- Product judgment Agent station only outputs product judgments.
- Product judgment package station owns same-product merge, confidence merge, and 70% candidate gate.
- Product judgment coverage must reach 90%; low coverage pauses task mapping.
- Task mapping Agent station only outputs task generation decisions.
- Task pool admission station owns dedupe, limit, and task pool writes.
- Frontend read model station owns current-run projections.
- Task pool acceptance station owns final count alignment.

一句话：V16.5 把被压进巨型 Agent 站里的流程拆回来，让每个断点都能被单独运行、单独验收、单独定位。
