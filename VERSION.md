# Current Version

```text
14.4.0
```

## V14.4 Meaning

V14.4 is a structural task-chain update. It adds a stable TaskIntent contract between Agent output, task snapshots, task pool, and visible tasks.

Mainline:

```text
Agent judgment
  -> TaskIntent contract
  -> task snapshot
  -> task pool entry
  -> visible task
  -> task lifecycle
```

Core rules:

- Downstream services do not read raw Agent package internals directly.
- Task pool normalizes snapshots through TaskIntent before creating visible tasks.
- Legacy impact estimation reads `actionImpactInput.metrics` first.
- Mixed evidence formats must not break visible task creation.
- TaskIntent is the anti-corruption layer between V14+ and older task modules.
