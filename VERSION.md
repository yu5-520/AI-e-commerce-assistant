# Current Version

```text
12.8.3
```

## Release Contract

- FastAPI `app.version` must match this file.
- `versioning/VERSION.md` must match this file.
- `/api/health` version must match this file.
- `web_demo/index.html` asset query versions must match this file.
- README baseline must match this file.
- V12.8.3 means: V12.8.2 backend main-architecture forced gates + task card action surface and aggregate detail report closure. The task list must show a left time/order rail, one current human action plus persistent detail, and must not render review or recap buttons on operator task cards. The frontend must use backend `primaryTaskAction` / `visibleTaskActions` instead of raw `availableActions`. Aggregate tasks must have a stable Chinese detail report with affected products, trigger reason, lifecycle, evidence, authorization, recap cycles, and next step.
