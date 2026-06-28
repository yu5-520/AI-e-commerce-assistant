# Current Version

```text
12.7.1
```

## Release Contract

- FastAPI `app.version` must match this file.
- `versioning/VERSION.md` must match this file.
- `/api/health` version must match this file.
- `web_demo/index.html` asset query versions must match this file.
- README baseline must match this file.
- V12.7.1 means: V12.7 weight confidence policy + compact clustered task queue + task report fail-closed fallback. Repeated product tasks with the same store, action and reason are shown as one queue task in the frontend, with affected products kept in the detail report. Task report routes return structured fallback reports instead of HTTP 500.
