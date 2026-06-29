Current Version: 14.4.1

V14.4.1 TaskIntent PermissionEnvelope

Core chain:

`Agent judgment -> TaskIntent contract -> PermissionEnvelope -> task snapshot -> task pool entry -> visible task -> lifecycle stations`

Key updates:

- `task_intent_contract_service.py` now builds `permissionEnvelope` from structured budget and risk fields.
- `action_authorization_gate_service.py` now reads permission and budget from structured fields only.
- Approval no longer parses budget from product code, title, deadline, id, or free text.
- Normal `create_task_snapshot` tasks can enter `operator_execution` when the envelope allows it.
- High-risk, hard-action, manager-review, and over-budget tasks still enter `manager_approval`.

Boundary:

TaskIntent controls downstream task permission. Legacy task modules do not guess budget from text.
