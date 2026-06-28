# Current Version

```text
12.8.0
```

## Release Contract

- FastAPI `app.version` must match this file.
- `versioning/VERSION.md` must match this file.
- `/api/health` version must match this file.
- `web_demo/index.html` asset query versions must match this file.
- README baseline must match this file.
- V12.8 means: task lifecycle closed loop. A task must move through one task_id from generation, acceptance, evidence submission, manager review, automatic recap scheduling, recap completion, RAG candidate creation, RAG approval, and future task generation enhancement. Operators submit facts, the system schedules recap windows and reads follow-up metrics, and only approved/effective recap experience cards enhance later tasks.
