Current Version: 13.3.0

V13.3 Task Snapshot Station

This release adds the Task Snapshot Station as the formal decision package between Agent judgment and task pool.

Core rule:

- External report data still stops at the operating snapshot.
- V13.1 handoff still moves the snapshot into the task judgment line.
- Agent judgment results do not directly create visible tasks.
- V13.3 stores Agent judgment as a `task_snapshot` first.
- Task snapshots can represent create-task, manager-review, observe-only, or ignore-noise decisions.
- Task pool entry must be handled later by `task_pool_station`.

Key updates:

- Added `src/services/task_snapshot_station_service.py`.
- Added `src/api/routes/task_snapshots.py` with `/api/task-snapshots` APIs.
- Updated `src/api/main.py` to `13.3.0` and included task snapshot routes.
- Updated `station_registry_service.py` to register the Agent task judgment line:
  - `task_signal_station`
  - `rag_context_station`
  - `agent_judgment_station`
  - `task_snapshot_station`
- Updated `station_contract_service.py` with V13.3 task snapshot contracts.
- Added `task_snapshots` to runtime DB status and reset scope.

Current contract:

System facts and RAG context support Agent judgment. Agent judgment produces a task snapshot. A task snapshot is not yet a visible task. Later versions should move `snapshot_ready` records into `task_pool_station`, then continue task acceptance, submission, review, recap, and RAG feedback.
