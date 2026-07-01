# AI ERP 企业级电商经营 SaaS 底座

Current baseline: **V16.7 MVP Legacy Route Purge / V16.5 Station Alignment runtime**.

V16.7 keeps the V16 MVP file manifest and removes the first wave of old route pollution from active runtime. Git history is the archive; current files serve the MVP.

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

## Purged in V16.7

```text
src/api/routes/deprecated_stations.py
src/api/routes/v9_readiness.py
src/api/routes/v10_product.py
src/api/routes/architecture.py
src/api/routes/data_source_compat.py
src/api/routes/station_handoffs.py
src/api/routes/report_task_sync.py
src/api/routes/trends.py
```

Old station aliases were removed from `station_registry_service.py`. Only V16 station IDs can enter the current chain.

## Manifest files

```text
MVP_V16_FILE_MANIFEST.md
config/v16_mvp_file_manifest.json
scripts/check_v16_manifest.py
```

## Check remaining unmarked files

```bash
python scripts/check_v16_manifest.py
```

## Rule

```text
One station = one input contract + one output artifact + one acceptance metric.
Agent stations only produce Agent outputs.
System stations own package merge, admission, read models, and acceptance.
Low product-judgment coverage pauses task mapping.
Files outside the V16 manifest are deletion candidates for MVP cleanup.
```

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
