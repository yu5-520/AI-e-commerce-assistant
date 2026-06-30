# Current Version

```text
14.8.3
```

## V14.8.3 Meaning

V14.8.3 is the station-chain contract and metro-line visualization release.

Mainline:

```text
report import system
  -> background worker compute
  -> system product layered snapshot
  -> fullProductBundle assembly
  -> RAG volatility boundary context
  -> Agent product diagnosis soft routing
  -> task_generation_run is always recorded
  -> formal tasks optionally enter task_snapshot / task_pool
  -> frontend read model refresh
  -> data page renders metro-line chain status
```

Core rules:

- Chain completion is not the same as formal task count.
- Agent judgment may output zero formal tasks; that is a completed business result, not a broken pipeline.
- Every Agent judgment station run writes a `task_generation_runs_v14` row.
- The data page no longer shows a long engineering sync sentence. It renders a station line: 接入 / 建档 / 全量包 / 判断 / 任务 / 展示.
- Passed stations are green, the current station can flow, empty task output is a valid empty station, and only real technical failures should be red.
- Observe-only results stay out of `task_pool`, but they are counted in the chain status.
- `GET /api/view/data-line` is read-only and does not trigger compute.
