# Current Version

```text
16.23
```

## V16.23

System route context cleanup.

`src/api/routes/system.py` no longer imports the deleted `src.core.context` module. MVP keeps database status and explicit runtime cleanup routes; old production diagnostics return lightweight disabled projections until reintroduced through V16 contracts.

## Verify

```bash
python scripts/check_v16_manifest.py
```
