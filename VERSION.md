# Current Version

```text
12.3.0
```

## Release Contract

- FastAPI `app.version` must match this file.
- `versioning/VERSION.md` must match this file.
- `/api/health` version must match this file.
- `web_demo/index.html` asset query versions must match this file.
- README baseline must match this file.
- V12.3 means: V12.2 fact/layout stack + API contract patch + document governance cleanup. Current execution docs are separated from historical archive docs, `web_demo/` is the only active frontend, `frontend/` is marked deprecated, and deployment checks block version/document drift before ECS runs the wrong chain.
