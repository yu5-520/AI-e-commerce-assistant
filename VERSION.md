# Current Version

```text
16.17
```

## V16.17

Legacy ImportJob route removal.

`src/api/routes/import_jobs.py` and its old ImportJob worker services were removed from the active MVP runtime. Data import now uses the V16 `data_import.py` route only; task generation remains owned by station queue and Agent mainline.

## Verify

```bash
python scripts/check_v16_manifest.py
```
