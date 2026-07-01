# Current Version

```text
16.19
```

## V16.19

Module task-report route prune.

`src/api/routes/modules/task_report.py` was removed from the active modules router. Task details are now owned by the V16 task_pool, task_persistence, task_lifecycle and frontend read-model routes.

## Verify

```bash
python scripts/check_v16_manifest.py
```
