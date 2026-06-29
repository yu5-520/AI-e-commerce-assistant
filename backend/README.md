# Deprecated backend folder

This folder is no longer the runtime backend entrypoint.

## Current backend entrypoint

Run the application through FastAPI at:

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

On ECS, the systemd service should point to `src.api.main:app`, not to `backend/server.py`.

## Current product boundary

- API version: V12.11.1
- Frontend static files: `web_demo/`
- Main API router: `src/api/main.py`
- Task lifecycle: `src/services/task_lifecycle_state_machine_service.py`
- Task generation enhancement: `src/services/v1211_agent_sop_enhancement_service.py`
- Manual module task wrapper: `src/services/v1211_manual_task_package_service.py`

## Why this file remains

The old local MVP backend documented `python backend/server.py` and `/api/generate`.
That flow is deprecated and must not be used for the current AI ERP Operating Advisor demo.

If deployment scripts, README snippets, or service files still reference `backend/server.py`, treat them as stale configuration and replace them with `src.api.main:app`.
