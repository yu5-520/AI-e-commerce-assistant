Current Version: 12.11.4

V12.11.4 UID helper startup hotfix

This is a startup hotfix for V12.11.3.

Root cause:

- `task_evidence_repository_service.py` and task evidence code import `src.services.uid.make_id`.
- `src.services.uid` did not exist in the repository.
- `python scripts/verify_release.py` failed while importing `src.api.main`.
- FastAPI could not start on ECS, so Nginx kept returning 502 Bad Gateway.

Fix:

- Added `src/services/uid.py` as a tiny compatibility helper.
- Added `make_id(prefix)` based on Python stdlib `uuid` and `datetime`.
- Bumped API version to `12.11.4`.

Current contract remains:

System extracts data changes. Agent generates operating judgment and executable SOP. Operators execute and submit evidence. The system performs automatic recap after later report or interface data refreshes and writes the result to daily reports, weekly reports and the recap library.
