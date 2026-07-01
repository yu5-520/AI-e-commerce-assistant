Current Version: 16.22

V16.22 legacy pipeline route removal.

The old src/api/routes/pipeline.py route was removed from active runtime. Task generation is owned by the V16 data_import, station_queue, Agent mainline and task_pool routes.

Verify with scripts/check_v16_manifest.py
