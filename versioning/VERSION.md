Current Version: 12.11.3

V12.11.3 json dependency startup hotfix

This is a startup hotfix for V12.11.2.

Root cause:

- `src/services/task_evidence_repository_service.py` imported `src.services.json_store`.
- `src.services.json_store` does not exist in the repository.
- `python scripts/verify_release.py` failed while importing `src.api.main`.
- FastAPI could not start on ECS, so Nginx kept returning 502 Bad Gateway.

Fix:

- Removed the missing `src.services.json_store` dependency.
- Replaced it with Python stdlib `json`.
- Kept evidence audit persistence dependency-light and safe for the demo runtime.
- Bumped API version to `12.11.3`.

Current contract remains:

System extracts data changes. Agent generates operating judgment and executable SOP. Operators execute and submit evidence. The system performs automatic recap after later report or interface data refreshes and writes the result to daily reports, weekly reports and the recap library.
