# Current Version

```text
16.3
```

## V16.3 Meaning

V16.3 is the current-run real task-pool acceptance release.

It keeps the V16.2 real product judgment Agent and real RAG task mapping Agent, then adds the MVP验收闸门:

```text
latest taskGenerationRun
  -> latestRun.dataVersion
  -> latestRun.taskPoolCreatedCount
  -> task_pool_entries WHERE data_version = latestRun.dataVersion
  -> frontend_task_view WHERE data_version = latestRun.dataVersion
  -> frontend_task_detail_view WHERE data_version = latestRun.dataVersion
  -> acceptance pass / fail
```

Core rules:

- `/api/view/task-pool-acceptance` is read-only and never generates tasks.
- Data-line `formalTaskCount` must equal the latest run `taskPoolCreatedCount`.
- Latest run `taskPoolCreatedCount` must equal current `task_pool_entries` count.
- Current `task_pool_entries` count must equal current `frontend_task_view` count.
- Every visible current task must have a matching `frontend_task_detail_view` row.
- `frontend_task_view` must not keep old dataVersion rows.
- Historical `task_pool_entries` may remain in storage, but must not enter the current execution queue.
- If counts do not align, `/api/view/data-line` enters attention and surfaces the acceptance mismatches.
- No mismatch is repaired by fake tasks or local template fallback.

一句话：V16.3 不是继续生成任务，而是证明“数据页任务数 = 任务池本轮任务数 = 任务页执行任务数 = 详情页任务数”；对不上就暴露断点，不再用刷新或垫底内容遮住问题。
