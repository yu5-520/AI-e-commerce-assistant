# Current Version

```text
14.6.2
```

## V14.6.2 Meaning

V14.6.2 upgrades the station queue from asynchronous batch processing to streaming task pool fast lane.

Mainline:

```text
report import system
  -> enqueue task generation
  -> background station queue worker
  -> Agent judgment
  -> task_snapshot fast lane
  -> task_pool fast lane
  -> task lifecycle system
```

Core rules:

- Mature tasks do not wait for the whole dataVersion batch to finish.
- `task_pool_station` has the highest queue priority.
- `task_snapshot_station` has the second-highest queue priority.
- Agent judgments with pending task snapshots immediately stream into the fast lane.
- The worker still runs outside upload requests and keeps bounded per-tick execution.
- Task lifecycle starts as soon as a task pool entry is created.
