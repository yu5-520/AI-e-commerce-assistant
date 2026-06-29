Current Version: 12.14.0

V12.14.0 Station Contract & Ops Diagnostic Train

This release upgrades pipeline stations from a flow concept into standard addressable station modules.

Core rule:

- Every station has a registered identity, stage, backend module, frontend module, contract, health surface and standard interface.
- Frontend and backend should talk through Station Interface and pipeline gates instead of direct internal service coupling.
- The Ops Diagnostic Train runs diagnostic station checks without carrying real business data.
- Business pages still read snapshots and task packages only.

Key updates:

- Added `src/services/station_registry_service.py` for station registration and ordering.
- Added `src/services/station_contract_service.py` for input/output contracts, station health, standard run/replay and gate views.
- Added `src/services/ops_diagnostic_train_service.py` for diagnostic train runs and station checks.
- Added `src/api/routes/stations.py` with `/api/stations` standard station interfaces.
- Added `src/api/routes/ops.py` with `/api/ops/train/run`, latest run, run history and station health APIs.
- Updated `src/api/main.py` to include station and ops routers and bump API version to `12.14.0`.
- Updated `web_demo/modules/system-status/page.js` with station health and Ops Diagnostic Train UI.
- Updated `src/services/system_service.py` so reset/db-status include ops diagnostic tables.
- Bumped frontend cache to `12.14.0`.

Current contract:

The business train carries real data. The ops train carries diagnostic inputs only. Each station exposes contract, health, run, replay, gates and latest through a standard interface. The ops train checks these interfaces to locate broken stations before users discover failures by opening pages.
