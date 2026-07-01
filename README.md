# AI ERP 企业级电商经营 SaaS 底座

Current baseline: **V16.21 Module Todo Route Prune / V16 MVP runtime**.

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

## Current verification entry

```bash
python scripts/check_v16_manifest.py
```

## V16.21 rule

The legacy `modules/todo.py` route is removed from active runtime. Task list, task details and lifecycle actions are served by the V16 task_pool, task_persistence, task_lifecycle and frontend read-model routes.

## Entry points

```text
web_demo/
src/api/main.py
VERSION.md
versioning/VERSION.md
MVP_V16_FILE_MANIFEST.md
```

## Deploy

```bash
bash scripts/deploy_fast.sh
```
