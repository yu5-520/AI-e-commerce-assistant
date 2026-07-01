# AI ERP 企业级电商经营 SaaS 底座

Current baseline: **V16.5 Station Alignment**.

V16.5 aligns the station registry, contract, queue, adapter, and data-line to one split execution chain.

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

## Rule

```text
One station = one input contract + one output artifact + one acceptance metric.
Agent stations only produce Agent outputs.
System stations own package merge, admission, read models, and acceptance.
Low product-judgment coverage pauses task mapping.
```

## Entry points

```text
web_demo/
src/api/main.py
VERSION.md
versioning/VERSION.md
```

## Deploy

```bash
bash scripts/deploy_fast.sh
```
