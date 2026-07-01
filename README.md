# AI ERP 企业级电商经营 SaaS 底座

Current baseline: **V16.6 MVP File Marking / V16.5 Station Alignment runtime**.

V16.6 adds the V16 MVP file manifest. From this point, the working tree is treated as a current MVP repository, not a historical version archive. Git history keeps old evidence; current files must either be V16-marked or reviewed for deletion.

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

## V16 file markers

```text
V16_KEEP      Current MVP mainline files.
V16_SUPPORT   Runtime support required by current MVP files.
V16_FRONTEND  Current web demo entry and modules.
V16_DOC       Current documentation only.
V16_TOOL      Current repository governance scripts.
UNMARKED      Deletion candidate after import check.
```

## Manifest files

```text
MVP_V16_FILE_MANIFEST.md
config/v16_mvp_file_manifest.json
scripts/check_v16_manifest.py
```

## Check before purge

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
