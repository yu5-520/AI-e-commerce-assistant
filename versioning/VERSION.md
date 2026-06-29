Current Version: 12.13.1

V12.13.1 Legacy Trigger Cleanup

This release removes the old trigger points that were still affecting the V12.13 station pipeline.

Core rule:

- Import endpoints only materialize data stations and write pipeline gates.
- Import endpoints do not synchronously generate tasks.
- Dashboard and operating pages read snapshots instead of report projections.
- Todo GET is read-only; lifecycle actions are explicit.
- Demo reset clears pipeline gates and operating-unit snapshots.

Removed or disabled old flow effects:

- `data_import.py` no longer calls import-side `generate_risk_tasks_for_signals`.
- Legacy import hooks `attach_v104_import_sync`, `attach_v107_operating_profile`, `attach_v108_tag_change_tasks`, and `attach_v116_import_closed_loop` are disabled from the import request path.
- `_attach_v62_trend_and_risk_sync` is retained as a no-op compatibility function and cannot generate tasks.
- `web_demo/core/api-client.js` no longer runs full module refresh after import.
- `dashboard_service.py` no longer calls `projection_summary`, `projected_products`, or `projected_report_groups`.
- `system_service.py` now clears `operating_unit_snapshots` and `pipeline_stage_gates`.
- `GET /api/modules/todo` no longer clusters or auto-accepts tasks; use `POST /api/modules/todo/lifecycle/sync` for explicit lifecycle sync.

Current contract:

Report upload → parsed rows → metric facts → operating objects → operating-unit snapshot. Task generation is triggered only by `/api/pipeline/data-versions/{data_version}/tasks/generate`. Agent/RAG/LLM enhancement stays in the task station, and RAG feedback is the only learning loop.
