# Current Version

```text
16.22
```

## V16.22

Legacy pipeline route removal.

`src/api/routes/pipeline.py` was removed from active runtime. V16 task generation is owned by data_import, station_queue, Agent mainline and task_pool routes. Do not restore v142/v143 task mainline services.

## Verify

```bash
python scripts/check_v16_manifest.py
```
