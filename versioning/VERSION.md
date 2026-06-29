Current Version: 13.7.0

V13.7 Full Task Lifecycle Stations

This release completes the V13 task lifecycle station plan:

- V13.5 Task Acceptance / Assignment Station
- V13.6 Submission / Review Station
- V13.7 Recap / RAG Feedback Station

Core rule:

- Task Pool Station only creates visible task-pool tasks.
- Acceptance and assignment are explicit lifecycle stations.
- Submission records operator evidence, then advances the lifecycle state machine.
- Review records manager review, then advances to return or recap scheduling.
- Recap scheduling, recap completion and RAG candidate creation are explicit lifecycle stations.
- Todo pages are now projections and operation entrances, not hidden lifecycle owners.

Key updates:

- Added `src/services/task_acceptance_assignment_station_service.py`.
- Added `src/services/task_submission_review_station_service.py`.
- Added `src/services/task_recap_rag_station_service.py`.
- Added `src/api/routes/task_lifecycle_stations.py`.
- Updated `src/api/main.py` to `13.7.0` and included task lifecycle station routes.
- Updated `station_registry_service.py` with the full internal task lifecycle line.
- Updated `station_contract_service.py` with V13.7 lifecycle station contracts.

Current full chain:

External data line:

`import_station → report_parse_station → metric_fact_station → operating_object_station → operating_snapshot_station`

Agent judgment line:

`task_signal_station → rag_context_station → agent_judgment_station → task_snapshot_station`

Internal task lifecycle line:

`task_pool_station → task_acceptance_station / task_assignment_station → task_submission_station → task_review_station → recap_schedule_station → recap_complete_station → rag_feedback_station`

Current boundary:

The Station Registry and dedicated lifecycle APIs are V13.7-complete. Station Interface can still write standard gates for every station. The dedicated lifecycle APIs perform the real task operations for acceptance, assignment, submission, review, recap and RAG feedback.
