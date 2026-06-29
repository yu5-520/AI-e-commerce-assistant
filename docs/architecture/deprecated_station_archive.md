# Deprecated Station Archive

Version: V12.14.2

## Purpose

Deprecated Station Archive stores old files, old hooks, old compatibility routes and old documents so they do not pollute the business mainline architecture.

## Three Categories

### A. Delete directly

Files can be deleted when they are not imported, not routed, not loaded by frontend, not used by adapter, and recoverable from Git history.

### B. Archive reference

Files can remain as archived references when their old logic is useful for migration but they must not be imported by mainline code.

### C. Station adapter whitelist

Legacy services can be temporarily used behind Station Adapter. They must not be called by old routes, frontend pages or main.py.

## Current High-Risk Archive Items

- `src/services/v112_task_chain_fix_service.py`
- `src/services/v1211_agent_sop_enhancement_service.py`
- `src/services/v1212_rag_llm_agent_service.py`

## Current Adapter Dependencies

- `src/services/risk_task_service.py` → `task_signal_station`
- `src/services/operating_unit_snapshot_service.py` → `operating_snapshot_station`
- `src/services/metric_fact_store_service.py` → `metric_fact_station`

## API

```http
GET /api/deprecated-stations
GET /api/deprecated-stations/risks
GET /api/deprecated-stations/mainline-check
GET /api/deprecated-stations/{legacy_id}
```

## Ops Train Check

Ops Diagnostic Train runs `deprecated_mainline_leak` before station checks. If archived files are found in main.py, Station Registry, frontend entry or direct pipeline service imports, the train reports a failed stage.
