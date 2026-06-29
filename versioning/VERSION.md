Current Version: 12.11.1

V12.11.1 lifecycle cleanup release

This release keeps V12.11 system change pack + Agent SOP + automatic recap, then cleans old files and old write paths that were still occupying live flow positions.

Fixed chain points:

- `submit_task_evidence` now only stores evidence and no longer calls the legacy `submit_task` status writer.
- `/api/modules/todo/{task_id}/submit-evidence` stores evidence first, then uses the unified lifecycle state machine to submit.
- `split` and `assign` now route through `task_lifecycle_state_machine_service` instead of direct `update_task`.
- Product, competitor, listing, traffic and report manual task creation endpoints now wrap old flat module payloads into V12.11 SOP task packages.
- `backend/README.md` is marked deprecated and points to `src.api.main:app`.
- API, frontend cache, todo action surface, lifecycle state machine, repository write path and risk task facade versions are aligned to V12.11.1.

Current contract:

System extracts data changes. Agent generates operating judgment and executable SOP. Operators execute and submit evidence. The system performs automatic recap after later report or interface data refreshes and writes the result to daily reports, weekly reports and the recap library.
