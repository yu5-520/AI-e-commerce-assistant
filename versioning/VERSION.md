Current Version: 12.14.1

V12.14.1 Station Contract Cleanup

This release closes the remaining gap between the old Pipeline route and the V12.14 Station Interface.

Core rule:

- `/api/pipeline` is now a compatibility layer.
- Pipeline task generation and snapshot generation delegate to Station Contract instead of calling business services directly.
- Pipeline gates separate business gates from Ops Diagnostic Train gates with `run_type` and `is_diagnostic`.
- Business summaries hide diagnostic gates by default.
- Station Contract uses real adapters for `operating_snapshot_station` and `task_signal_station`; diagnostic runs remain simulated.
- Global startup Agent/RAG monkey patches are removed from `main.py` mainline and should be executed only by explicit station flow.

Key updates:

- Added `src/services/station_adapter_service.py` for narrow real adapters behind Station Interface.
- Updated `src/services/station_contract_service.py` to use station adapters and write isolated business/diagnostic gates.
- Updated `src/services/pipeline_gate_service.py` to add `run_type` and `is_diagnostic`, and default-filter diagnostic gates.
- Updated `src/api/routes/pipeline.py` into a Station Interface compatibility layer.
- Updated `src/api/routes/stations.py` to support `includeDiagnostic` for gate views.
- Updated `src/api/main.py` to `12.14.1` and remove startup monkey-patch execution from the mainline.
- Bumped frontend cache to `12.14.1`.

Current contract:

The business train runs through Station Interface. The old pipeline URLs remain available for compatibility, but they forward into the relevant station. Ops Diagnostic Train records stay isolated from business gate summaries unless explicitly requested with `includeDiagnostic=true` or a `DIAG-*` data version.
