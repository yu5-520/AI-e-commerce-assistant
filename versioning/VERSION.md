Current Version: 13.1.0

V13.1 Agent-Guided Snapshot Task Handoff

This release starts V13 by connecting the external data station line to the internal task judgment line without restoring old task-generation hooks.

Core rule:

- External report data becomes metric facts, operating objects and operating snapshots.
- Operating snapshots do not directly create tasks.
- A snapshot creates a light `station_handoff` into the task judgment line.
- Task generation remains blocked until RAG context and Agent judgment decide whether a task snapshot should be created.
- V13.1 records the handoff as `pending_agent_judgment` instead of using system-only rigid rules.

Key updates:

- Added `src/services/snapshot_task_handoff_service.py`.
- Added `src/api/routes/station_handoffs.py` with `/api/station-handoffs` APIs.
- Updated `src/api/main.py` to `13.1.0` and included station handoff routes.
- Added `station_handoffs` to runtime DB status and reset scope.
- Updated frontend API client so import refresh creates a snapshot-to-task-judgment handoff after data refresh.

Current contract:

The data line stops at the operating snapshot. V13.1 creates the bridge into the task judgment line. V13.2 should consume the handoff, call RAG context and Agent judgment, and only then create task snapshots.
