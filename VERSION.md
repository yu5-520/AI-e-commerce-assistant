# Current Version

```text
12.9.1
```

## Release Contract

- FastAPI `app.version` must match this file.
- `versioning/VERSION.md` must match this file.
- `/api/health` version must match this file.
- `web_demo/index.html` asset query versions must match this file.
- README baseline must match this file.
- V12.9.1 means: V12.9 lifecycle state machine + auto-accept and idempotent repository-aware lifecycle. Operator permission-in tasks that do not require manager/owner review must be auto-accepted into `处理中` / `accepted` when the todo queue is read. Manual accept becomes idempotent: if the task is already in `处理中` or a later stage, it returns the latest projection without writing duplicate receive logs. The lifecycle state machine must read and hydrate tasks from SQLite TaskRepository when the in-memory task pool is empty, so the visible task list, accept/submit actions, task detail report and event log use the same primary task_id.
