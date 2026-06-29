Current Version: 14.3.1

V14.3.1 Signal Handoff Fix

Core chain:

`report import -> operating_snapshot_station -> system_product_snapshot_station -> product_signal_snapshot_station -> task_signal_station -> rag_context_station -> agent_judgment_station -> task_snapshot_station -> task_pool_station -> lifecycle stations`

Key updates:

- `signal_pool_service.py` now normalizes full product signal packages to `pending_rag_agent` before Agent consumption.
- Existing pending package rows with `pending_agent_judgment` are repaired when signal pool regenerates.
- `health.py`, `main.py`, `VERSION.md`, `versioning/VERSION.md`, and `web_demo/index.html` are aligned to 14.3.1.

Runtime counters to verify:

`productSnapshotCount`, `productSignalPackageCount`, `signalCount`, `judgmentCount`, `taskSnapshotCount`, `createdTaskCount`, `budgetLedgers`.

Boundary:

The system generates and queues full signal packages. RAG defines operation-value and budget boundaries. Agent judges. The system reserves budget and controls task lifecycle.
