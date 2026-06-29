# Current Version

```text
12.9.0
```

## Release Contract

- FastAPI `app.version` must match this file.
- `versioning/VERSION.md` must match this file.
- `/api/health` version must match this file.
- `web_demo/index.html` asset query versions must match this file.
- README baseline must match this file.
- V12.9.0 means: task lifecycle state machine unified write entrance. Accept, submit, manager review, recap completion and RAG candidate creation must flow through `task_lifecycle_state_machine_service`. The same primary `task_id` must be used across the visible task queue, task detail report, lifecycle event log, SQLite mirror and frontend task store. Accepting a task must move it to `处理中` / `accepted`, create an `operator_accepted` event, update the persistent mirror, return the latest task projection, and make the frontend button change from 接收 to 提交.
