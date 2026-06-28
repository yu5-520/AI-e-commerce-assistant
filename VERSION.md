# Current Version

```text
12.8.1
```

## Release Contract

- FastAPI `app.version` must match this file.
- `versioning/VERSION.md` must match this file.
- `/api/health` version must match this file.
- `web_demo/index.html` asset query versions must match this file.
- README baseline must match this file.
- V12.8.1 means: V12.8 task lifecycle closed loop + frontend/backend contract alignment + document governance cleanup. The frontend must trust backend clustered task objects and must not re-cluster tasks locally. The API client must expose lifecycle summary and recap completion endpoints. `module_task_service.create_task()` must attach the generated lifecycle stage. Current execution docs must describe V12.8.1 lifecycle contracts, not V12.3/V12.7-era flows.
