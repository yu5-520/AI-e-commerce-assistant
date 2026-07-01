# Current Version

```text
16.20
```

## V16.20

Module agents route prune.

`src/api/routes/modules/agents.py` was removed from the active modules router. Old V10/V14 candidate/playbook task-agent logic is no longer imported by FastAPI. Real Agent execution remains inside the V16 product judgment and task mapping mainline.

## Verify

```bash
python scripts/check_v16_manifest.py
```
