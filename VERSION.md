# Current Version

```text
16.25
```

## V16.25

UID utility restore.

`src/services/uid.py` was added as a thin V16 support utility for task evidence and lifecycle audit IDs. This keeps the V16 task submission evidence chain active without restoring old workflow modules.

## Verify

```bash
python scripts/check_v16_manifest.py
```
