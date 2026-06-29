# Current Version

```text
14.4.1
```

## V14.4.1 Meaning

V14.4.1 adds TaskIntent PermissionEnvelope.

Mainline:

```text
Agent judgment
  -> TaskIntent contract
  -> PermissionEnvelope
  -> task snapshot
  -> task pool entry
  -> visible task
  -> task lifecycle
```

Core rules:

- Task approval reads structured permission fields.
- Budget reads TaskIntent budget fields only.
- Product code, title, deadline, id, and free text cannot become budget.
- `create_task_snapshot` can enter `operator_execution` when the envelope allows it.
- `manager_review_required`, high risk, hard actions, and over-budget tasks enter `manager_approval`.
