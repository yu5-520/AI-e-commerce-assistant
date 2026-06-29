Current Version: 14.2.0

V14.2 System Product Snapshot Signal Mainline

This release aligns the product module state and task signal generation path.

Core chain:

`report import -> operating_snapshot_station -> system_product_snapshot_station -> product_signal_snapshot_station -> task_signal_station -> rag_context_station -> agent_judgment_station -> task_snapshot_station -> task_pool_station -> lifecycle stations`

Key updates:

- Added `src/services/system_product_snapshot_service.py`.
- Added `src/services/product_signal_snapshot_service.py`.
- Added `src/services/v142_task_mainline_service.py`.
- Updated `src/services/signal_pool_service.py` to consume product signal snapshots.
- Updated `src/services/station_registry_service.py` with snapshot signal stations.
- Updated `src/services/station_contract_service.py` with V14.2 contracts.
- Updated `src/services/station_adapter_service.py` with real snapshot signal adapters.
- Updated `src/api/routes/pipeline.py` to run the V14.2 mainline.
- Updated `src/api/routes/data_import.py` to run the V14.2 mainline after imports.
- Updated `src/api/main.py` to `14.2.0`.
- Added `docs/V14_2_UPDATE_SUMMARY.md`.
- Added `docs/V14_OLD_CHAIN_ISOLATION.md`.

Runtime counters:

`productSnapshotCount`, `productSignalCount`, `signalCount`, `judgmentCount`, `taskSnapshotCount`, `createdTaskCount`, `observeOrNoiseCount`.

Boundary:

Legacy routes may remain for archive, compatibility or diagnostics. The visible task path must pass through `task_snapshot_station`.
