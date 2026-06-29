Current Version: 12.9.0

V12.9.0 task lifecycle state machine unified write entrance

This release makes task_lifecycle_state_machine_service the only write entrance for visible task lifecycle transitions. Accept, submit, manager review, recap completion and RAG candidate creation update status, lifecycle stage, event log, SQLite mirror and frontend task projection on the same primary task_id.
