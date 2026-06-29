Current Version: 14.3.0

V14.3 Full Product Signal Package Mainline

Core chain:

`report import -> operating_snapshot_station -> system_product_snapshot_station -> product_signal_snapshot_station -> task_signal_station -> rag_context_station -> agent_judgment_station -> task_snapshot_station -> task_pool_station -> lifecycle stations`

Key updates:

- `system_product_snapshot_service.py` now separates product profile snapshot, product metric snapshot and Agent package seed.
- `product_signal_snapshot_service.py` now creates full product signal packages for all products, including normal-state packages.
- `signal_pool_service.py` now queues full signal packages instead of only abnormal items.
- `operation_budget_service.py` adds task budget estimation and budget ledger support.
- `agent_judgment_station_service.py` now includes operation budget, SOP and evidence requirements in Agent judgments.
- `v142_task_mainline_service.py` remains as a compatibility name, but now runs the V14.3 mainline and caps Agent batch size at 20 packages.
- `station_adapter_service.py`, `station_registry_service.py`, `station_contract_service.py`, `pipeline.py`, and `main.py` are updated to V14.3.

Runtime counters:

`productSnapshotCount`, `productSignalPackageCount`, `productSignalCount`, `signalCount`, `judgmentCount`, `taskSnapshotCount`, `createdTaskCount`, `observeOrNoiseCount`.

Boundary:

The system generates and queues full signal packages. RAG defines operation-value and budget boundaries. Agent judges. The system reserves budget and controls task lifecycle.
