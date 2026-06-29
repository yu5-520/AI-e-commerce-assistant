# Current Version

```text
14.2.0
```

## Release Contract

- FastAPI `app.version` must match this file.
- `versioning/VERSION.md` must match this file.
- `/api/health` version must match this file.
- `web_demo/index.html` asset query versions must match this file.
- README baseline must match this file.

## V14.2 Meaning

V14.2 means that report import, product state snapshot, product change snapshot, signal pool, RAG context, Agent judgment, task snapshot and task pool are aligned as one mainline.

Mainline:

```text
report import
  -> operating snapshot
  -> system product snapshot
  -> product signal snapshot
  -> signal pool
  -> RAG context
  -> Agent judgment
  -> task snapshot
  -> task pool
  -> task lifecycle
```

Legacy paths may remain for archive, compatibility and diagnostics, but the visible task path must pass through `task_snapshot_station`.
