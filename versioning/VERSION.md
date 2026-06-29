Current Version: 13.4.0

V13.4 Task Pool Station

This release adds Task Pool Station, which consumes eligible V13.3 task snapshots and creates visible lifecycle tasks.

Core rule:

- V13.3 task snapshots remain the formal Agent decision package.
- Only `create_task_snapshot` and `manager_review_required` snapshots can enter the task pool.
- `observe_only` and `ignore_noise` snapshots stay as judgment records and never create visible tasks.
- Task Pool Station creates the visible task package and records the pool entry.
- Task Pool Station does not accept, assign, submit, review, recap or write RAG feedback.
- Those actions continue in later lifecycle stations.

Key updates:

- Added `src/services/task_pool_station_service.py`.
- Added `src/api/routes/task_pool.py` with `/api/task-pool` APIs.
- Updated `src/api/main.py` to `13.4.0` and included task pool routes.
- Updated `station_registry_service.py` with `task_pool_station`.
- Updated `station_contract_service.py` with V13.4 task pool contracts.
- Updated `station_adapter_service.py` with a real adapter for `task_pool_station`.
- Added `task_pool_entries` to runtime DB status and reset scope.

Current contract:

The business chain is now: external data becomes an operating snapshot; the snapshot enters task judgment; Agent judgment becomes a task snapshot; eligible task snapshots enter the task pool. Next versions should split acceptance/assignment, submission/review, and recap/RAG feedback into lifecycle stations.
