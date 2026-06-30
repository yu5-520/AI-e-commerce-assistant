# Current Version

```text
14.8.0
```

## V14.8 Meaning

V14.8 separates frontend reads from backend compute and turns task handoff into a streaming pipeline.

Mainline:

```text
report import system
  -> background worker compute
  -> system product layered snapshot
  -> fullProductBundle assembly
  -> RAG volatility boundary context
  -> Agent product diagnosis soft routing
  -> mature judgment immediately creates V11.8 SOP task snapshot
  -> mature task immediately enters task pool
  -> frontend read model refresh
  -> frontend reads /api/view/* only
```

Core rules:

- Frontend page switching reads cached read models only.
- `/api/view/*` endpoints do not run materialize, generate, enqueue, Agent judgment, worker execution, or task sync.
- Worker compute writes results into `frontend_*_view` tables after key stations complete.
- One mature Agent judgment can stream into task snapshot and task pool immediately; it does not wait for the full worker batch.
- Observe, evidence-only, data-gap, and merge routes do not enter the formal task pool.
- Formal task output still remains the repository V11.8 SOP package.
- SQLite uses WAL and busy_timeout to reduce read/write blocking on low-config ECS.
