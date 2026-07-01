# AI ERP 企业级电商经营 SaaS 底座

Current baseline: **V16.8 MVP Purge Planner / V16.5 Station Alignment runtime**.

V16.8 keeps the V16.7 legacy route purge and upgrades the V16 manifest checker into a safe one-command purge tool for remaining unmarked files. Git history is the archive; current files serve the MVP.

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

## Purge remaining unmarked files

Review plan first:

```bash
python scripts/check_v16_manifest.py --write-plan
cat /tmp/v16_purge_plan.sh
bash /tmp/v16_purge_plan.sh
```

Direct local purge:

```bash
python scripts/check_v16_manifest.py --purge
```

The purge script uses `git rm` and does not commit automatically.

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
