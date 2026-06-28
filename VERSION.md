# Current Version

```text
12.6.1
```

## Release Contract

- FastAPI `app.version` must match this file.
- `versioning/VERSION.md` must match this file.
- `/api/health` version must match this file.
- `web_demo/index.html` asset query versions must match this file.
- README baseline must match this file.
- V12.6.1 means: V12.6 RAG operating action permission gate + task-store/action bridge hotfix. Product pages and other modules can safely call `findOpenTask` from either `AppTaskStore` or `AppTaskActions`; stale cached action bridges no longer break product archive rendering.
