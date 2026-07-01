# Current Version

```text
16.21
```

## V16.21

Module todo route prune.

`src/api/routes/modules/todo.py` was removed from the active modules router. Task list, task details and lifecycle actions are now owned by the V16 task_pool, task_persistence, task_lifecycle and frontend read-model routes.

## Verify

```bash
python scripts/check_v16_manifest.py
```
