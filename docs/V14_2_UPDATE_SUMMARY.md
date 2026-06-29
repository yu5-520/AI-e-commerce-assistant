# V14.2 Update Summary

## Theme

V14.2 changes task signal generation from a low-level fact-table scan to a system-snapshot comparison chain.

Mainline:

```text
report upload
  -> operating snapshot
  -> system product snapshot
  -> product signal snapshot
  -> signal pool
  -> RAG context
  -> Agent judgment
  -> task snapshot
  -> task pool
  -> task lifecycle
```

## Core Fix

The product module already updates from imported rows and system projections. Therefore the task signal layer must consume the same system product state.

V14.2 adds two explicit stations:

- `system_product_snapshot_station`
- `product_signal_snapshot_station`

The task signal station now consumes product signal snapshots instead of scanning `product_metric_facts` as the mainline.

## New Services

### `src/services/system_product_snapshot_service.py`

Freezes the product state produced by `projected_products()`.

Snapshot fields include:

- product identity
- store identity
- inventory
- payment amount
- gross margin
- ROI
- click rate
- conversion rate
- refund rate
- ad spend
- organic / paid visitors
- source data versions
- source datasets
- metric facts

### `src/services/product_signal_snapshot_service.py`

Compares the current system product snapshot with the previous snapshot.

Signal examples:

- `product_newly_seen`
- `product_missing_from_latest`
- `product_inventory_changed`
- `product_payment_changed`
- `product_margin_changed`
- `product_roi_changed`
- `product_click_changed`
- `product_conversion_changed`
- `product_refund_changed`
- `product_ad_spend_changed`

### `src/services/v142_task_mainline_service.py`

Shared orchestrator for import hooks and the pipeline route.

It runs:

```text
operating_snapshot_station
system_product_snapshot_station
product_signal_snapshot_station
task_signal_station
rag_context_station
agent_judgment_station
task_snapshot_station
task_pool_station
```

## Updated Files

- `src/services/signal_pool_service.py`
  - consumes product signal snapshots
  - no longer uses low-level fact scanning as the task signal mainline

- `src/services/station_registry_service.py`
  - registers `system_product_snapshot_station`
  - registers `product_signal_snapshot_station`

- `src/services/station_contract_service.py`
  - adds V14.2 station inputs/outputs
  - includes new stations in real adapter whitelist

- `src/services/station_adapter_service.py`
  - wires real adapters for product snapshot and product signal snapshot

- `src/api/routes/pipeline.py`
  - uses `run_v142_task_mainline()`

- `src/api/routes/data_import.py`
  - import endpoints now trigger V14.2 task mainline after data import and snapshot sync

- `src/api/main.py`
  - updates API version to `14.2.0`
  - updates mainline description

## Runtime Counters

Every import/task generation run should expose:

```text
productSnapshotCount
productSignalCount
signalCount
judgmentCount
taskSnapshotCount
createdTaskCount
observeOrNoiseCount
```

## Acceptance

If the product module shows imported products, then `productSnapshotCount` must be greater than zero.

If the same product changes across uploaded reports, then `productSignalCount` must be greater than zero.

If `productSignalCount > 0`, then `signalCount` and `judgmentCount` must also be greater than zero unless all signals were already processed.

## Principle

```text
fact table = evidence layer
system product snapshot = state layer
product signal snapshot = change layer
RAG = experience layer
Agent = judgment layer
task snapshot = lifecycle entry
task pool = execution entry
```
