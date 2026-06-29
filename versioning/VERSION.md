Current Version: 12.9.1

V12.9.1 auto-accept and idempotent repository-aware lifecycle

This release keeps the V12.9 lifecycle state machine and adds automatic acceptance for operator permission-in tasks, idempotent manual accept, and SQLite TaskRepository hydration. Visible task list, accept/submit actions, task detail report, event log and frontend task store must all use the same primary task_id.
