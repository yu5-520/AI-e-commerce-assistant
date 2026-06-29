Current Version: 12.13.0

V12.13.0 Pipeline Station Interface & Gate

This release changes the main flow from a page-triggered full recalculation loop into a one-way station pipeline.

Core rule:

- The main flow is a one-way freight-train chain.
- Each station receives the previous station's standard output, writes its own result, and records a gate.
- Frontend pages only read finished snapshots and task packages.
- The only learning loop is the recap-to-RAG feedback loop.

Key updates:

- Added `src/services/pipeline_gate_service.py` for stage gates keyed by tenant/user/data_version/stage/input_hash.
- Added `src/services/operating_unit_snapshot_service.py` so the operating page reads `operating_unit_snapshot` instead of recalculating report projections.
- Replaced `/api/modules/operating-unit` with a snapshot-only reader.
- Added `/api/modules/operating-unit/snapshot/rebuild` for explicit snapshot rebuilds.
- Added `/api/modules/operating-unit/pipeline/stages` for stage diagnostics.
- Added `src/api/routes/pipeline.py` with pipeline stage, snapshot and task-generation station endpoints.
- Included the pipeline router in `src/api/main.py`.
- Bumped frontend cache to `12.13.0`.

Why:

Before V12.13, opening the operating page could trigger `projection_summary`, `projected_products`, `projected_traffic`, task counters and heavy task-object reads in one synchronous request. After the second report upload, that could exceed the Nginx upstream timeout and return 504.

Current contract:

Report upload, parsing, metric facts, operating object mapping, operating-unit snapshot generation, task generation, Agent/RAG/LLM enhancement, operator submission, system auto-recap and RAG feedback are separate stations. Pages read station outputs; they do not trigger upstream processing.
