# Current Version

```text
16.8
```

## V16.8 Meaning

V16.8 is the MVP purge-planner release.

The first wave has already removed active legacy route imports, old route files and old station aliases. V16.8 upgrades the manifest checker into a safe purge tool so the remaining unmarked files can be removed in one local command after review.

## One-command local purge

```bash
python scripts/check_v16_manifest.py --write-plan
bash /tmp/v16_purge_plan.sh
```

Or, without writing a separate plan:

```bash
python scripts/check_v16_manifest.py --purge
```

The script uses `git rm` and does not commit automatically.

## Safety rules

```text
V16 manifest files are kept.
web_demo/ is kept.
Protected files such as .gitignore and .env.example are not deleted by --purge.
Unmarked files are deletion candidates unless promoted into config/v16_mvp_file_manifest.json.
```

## Current V16 mainline

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

Git history is the history archive. The current working tree only serves the MVP. V16.8 provides the safe one-command purge path for remaining unmarked files.
