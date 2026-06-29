Current Version: 12.14.2

V12.14.2 Deprecated Station Archive & Mainline Purity

This release adds a Deprecated Station Archive so old files, old hooks, old compatibility routes and old documents do not pollute the business mainline architecture.

Core rule:

- Business Mainline contains only clean stations.
- Ops Diagnostic Train checks stations and deprecated-file leaks.
- Deprecated Station Archive registers old files and allowed usage.
- Archive-only files must not be imported by main.py, Station Registry, frontend entry, or old routes.
- Legacy services still used by Station Adapter must be explicitly whitelisted.

Key updates:

- Added `src/services/deprecated_station_registry_service.py`.
- Added `src/api/routes/deprecated_stations.py` with `/api/deprecated-stations` APIs.
- Added clean `src/stations/agent_enhance_station/service.py` so the main station registry no longer points at V12.12 monkey-patch code.
- Updated `src/services/station_registry_service.py` to `12.14.2` and exclude deprecated files from the mainline registry.
- Updated `src/services/ops_diagnostic_train_service.py` so the ops train checks `deprecated_mainline_leak` before station checks.
- Updated `src/api/main.py` to `12.14.2` and include deprecated station archive routes.
- Added `docs/architecture/main_station_architecture.md` and `docs/architecture/deprecated_station_archive.md`.

Current contract:

The business train runs clean stations. The ops train runs diagnostics and deprecated leak checks. The deprecated station stores old files and compatibility rules only; it does not participate in the business route.
