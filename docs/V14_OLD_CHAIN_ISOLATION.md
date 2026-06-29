# V14 Old Chain Isolation

## Goal

V14+ has only one visible task generation path:

```text
system snapshot
  -> signal snapshot
  -> signal pool
  -> RAG context
  -> Agent judgment
  -> task snapshot
  -> task pool
  -> task lifecycle
```

Old files may remain for archive, compatibility, diagnostics, or candidate display. They must not create visible tasks or replace the snapshot/RAG/Agent mainline.

## Allowed Legacy Modes

Legacy code can be:

```text
archive_only
compatibility_noop
candidate_only
read_only_reference
diagnostic_reference
```

Legacy code cannot be:

```text
mainline_adapter
task_creator
task_pool_writer
agent_judgment_replacement
rag_context_replacement
lifecycle_owner
```

## Blocked Old Paths

### Manual module task wrapper

Blocked:

```text
module page button
  -> wrap_manual_task_payload
  -> create_task
  -> visible task pool
```

Allowed:

```text
module page button
  -> candidate or manual request
  -> task_snapshot_station
  -> task_pool_station
```

### Report task sync

Blocked:

```text
module_task_service.TASKS
  -> report_task_sync
  -> TaskRepository
```

`report_task_sync` may remain as a no-op compatibility route only.

### Module Agent direct write

Blocked:

```text
run_module_agent
  -> taskDrafts
  -> create_task_with_repository
```

Allowed output:

```text
analysis
candidate
playbook
```

### Risk task service as task signal adapter

Blocked:

```text
task_signal_station
  -> risk_task_service / operating_cadence_task_service
  -> direct task creation
```

Allowed:

```text
task_signal_station
  -> consume product_signal_snapshot
  -> write signal_pool
```

### Hard-coded operating SOP as final judge

Blocked as final decision logic:

```text
ROI/GMV quadrant hard gate
baseline hard block
fixed SOP as task creator
report count as task creation gate
```

Allowed as RAG context:

```text
company policy card
category baseline card
SOP card
historical recap card
```

## Mainline Whitelist

Task generation may use only:

```text
operating_snapshot_station
system_product_snapshot_station
product_signal_snapshot_station
task_signal_station
rag_context_station
agent_judgment_station
task_snapshot_station
task_pool_station
task_acceptance_station
task_submission_station
task_review_station
recap_complete_station
rag_feedback_station
```

## Forbidden Mainline Calls

These patterns must not appear in mainline routes/services:

```text
wrap_manual_task_payload
create_task(wrap_manual_task_payload
create_task_with_repository
generate_risk_tasks_for_signals
apply_v112_task_chain_fix
apply_v1211_agent_sop_enhancement
apply_v1212_rag_llm_agent
```

Allowed locations:

```text
docs
archive
tests
diagnostics
compatibility no-op route
```

Forbidden locations:

```text
src/api/routes/modules/* as direct task writer
src/api/routes/pipeline.py
src/services/station_adapter_service.py
src/services/station_contract_service.py
src/services/task_pool_station_service.py
src/api/main.py startup hooks
```

## Runtime Acceptance

A task run must expose:

```text
productSnapshotCount
productSignalCount
signalCount
judgmentCount
taskSnapshotCount
createdTaskCount
observeOrNoiseCount
```

If product pages show imported product data but `productSnapshotCount = 0`, the product snapshot station is broken.

If `productSnapshotCount > 0` but `productSignalCount = 0` across changed reports, the product signal snapshot station is broken.

If `productSignalCount > 0` but `signalCount = 0`, the task signal station is not consuming signal snapshots.

If `signalCount > 0` but `judgmentCount = 0`, the Agent judgment station is broken.

If `judgmentCount > 0` but `taskSnapshotCount = 0`, the task snapshot station is broken.

If `taskSnapshotCount > 0` but `createdTaskCount = 0`, the task pool station is broken.

## Final Rule

Old chains may remain for history, diagnostics and compatibility, but they must not create visible tasks, control lifecycle state, replace RAG, replace Agent judgment or bypass task snapshots.
