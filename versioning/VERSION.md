Current Version: 14.4.0

V14.4 TaskIntent Contract Layer

Core chain:

`Agent judgment -> TaskIntent contract -> task snapshot -> task pool entry -> visible task -> lifecycle stations`

Key updates:

- Added `src/services/task_intent_contract_service.py`.
- Updated `src/services/action_impact_estimation_service.py` to read standard `actionImpactInput.metrics` first and safely handle mixed evidence formats.
- Updated `src/services/task_pool_station_service.py` so task pool creates visible tasks through TaskIntent instead of passing raw Agent packages into legacy task code.
- Updated `src/api/main.py`, `src/api/routes/health.py`, `VERSION.md`, and this file to 14.4.0.

Boundary:

Agent output can evolve, but downstream task creation consumes the TaskIntent contract. This prevents future field-shape changes from breaking task pool and lifecycle code.
