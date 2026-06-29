# Main Station Architecture

Version: V12.14.2

## Rule

The main station architecture contains only the business mainline stations. Old files, old hooks, old compatibility routes and archived notes are not part of this document.

## Business Mainline

```text
import_station
→ report_parse_station
→ metric_fact_station
→ operating_object_station
→ operating_snapshot_station
→ task_signal_station
→ agent_enhance_station
→ evidence_station
→ auto_recap_station
→ rag_feedback_station
```

## Shared Interface

Every station is accessed through Station Interface:

```http
GET  /api/stations/{station_id}/contract
GET  /api/stations/{station_id}/health
GET  /api/stations/{station_id}/gates
GET  /api/stations/{station_id}/latest
POST /api/stations/{station_id}/run
POST /api/stations/{station_id}/replay
```

## Boundary

- Business pages read snapshots and task packages.
- Station Interface writes business gates.
- Ops Diagnostic Train writes diagnostic gates.
- Deprecated Station Archive stores legacy files and compatibility routes.

## Purity Requirement

Mainline stations must not point to archived V11/V12 monkey-patch files. If a legacy service is still needed, it must be used only behind Station Adapter and registered in Deprecated Station Archive.
