Current Version: 12.11.2

V12.11.2 evidence repository import hotfix

This is a startup hotfix for V12.11.1.

Root cause:

- `task_evidence_service.py` imported `src.services.task_evidence_repository_service`.
- The module did not exist in the repository.
- `python scripts/verify_release.py` failed while importing `src.api.main`.
- FastAPI could not start on ECS, so Nginx returned 502 Bad Gateway.

Fix:

- Added `src/services/task_evidence_repository_service.py`.
- Added `persist_evidence_submission(...)` for evidence audit persistence.
- Kept evidence persistence separate from task lifecycle status changes.
- Bumped API version to `12.11.2`.

Current contract remains:

System extracts data changes. Agent generates operating judgment and executable SOP. Operators execute and submit evidence. The system performs automatic recap after later report or interface data refreshes and writes the result to daily reports, weekly reports and the recap library.
