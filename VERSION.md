# Current Version

```text
14.8.1
```

## V14.8.1 Meaning

V14.8.1 is a breakpoint repair over V14.8. It keeps frontend read isolation, but fixes two regressions found in product detail and task generation.

Mainline:

```text
report import system
  -> background worker compute
  -> system product layered snapshot
  -> fullProductBundle assembly
  -> RAG volatility boundary context
  -> Agent product diagnosis soft routing
  -> mature judgment immediately creates V11.8 SOP task snapshot
  -> data-gap judgment creates formal data verification SOP task
  -> mature/data-gap task immediately enters task pool
  -> frontend read model refresh
  -> frontend reads /api/view/* and /api/modules/product bridge only
```

Core rules:

- Frontend page switching reads cached read models only.
- `/api/view/*` endpoints do not run materialize, generate, enqueue, Agent judgment, worker execution, or task sync.
- Product page can merge `frontend_product_view` with runtime product projection so SKU, product positioning, metric sections, traffic facts and missing-field summaries remain visible.
- One mature Agent judgment can stream into task snapshot and task pool immediately; it does not wait for the full worker batch.
- Missing core product facts are not hard blockers. They become formal data verification SOP tasks.
- Observe, evidence-only and merge routes stay outside the formal task pool, but must carry explicit reasons.
- Formal task output still remains the repository V11.8 SOP package.
- SQLite uses WAL and busy_timeout to reduce read/write blocking on low-config ECS.
