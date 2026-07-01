# AI ERP 企业级电商经营 SaaS 底座

Current baseline: **V16.10 Final Unmarked Purge / V16 MVP runtime**.

V16.10 removes the final broad group of unmarked legacy files from active repository state. Git history is the archive; current files serve the V16 MVP only.

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

## Manifest files

```text
MVP_V16_FILE_MANIFEST.md
config/v16_mvp_file_manifest.json
scripts/check_v16_manifest.py
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
