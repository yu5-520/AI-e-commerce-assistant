# Current Version

```text
14.3.1
```

## Release Contract

- FastAPI `app.version` must match this file.
- `versioning/VERSION.md` must match this file.
- `/api/health` version must match this file.
- `web_demo/index.html` asset query versions must match this file.
- README baseline must match this file.

## V14.3.1 Meaning

V14.3.1 fixes the signal handoff between full product signal packages and Agent judgment.

Mainline:

```text
report import
  -> operating snapshot
  -> system product layered snapshot
  -> full product signal packages
  -> signal package queue
  -> RAG operation-value context
  -> Agent budget judgment
  -> budgeted task snapshot
  -> task pool
  -> task lifecycle
```

Core fix:

- Product signal packages may be born as `pending_agent_judgment`.
- Signal pool now normalizes Agent-ready packages to `pending_rag_agent`.
- Agent judgment station consumes `pending_rag_agent`.
- Existing pending package rows are repaired when the signal pool is regenerated.

Core rules:

- The system does not drop normal products before Agent judgment.
- Agent judges operation value under RAG boundaries.
- ROAS increase/decrease, campaign apply, replenishment and creative tests all carry estimated budget.
- High-risk tasks enter manager review and do not consume ordinary operator budget.
- A task enters lifecycle as soon as it is generated; the Agent continues judging the next batch.
