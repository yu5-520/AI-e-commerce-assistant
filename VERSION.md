# Current Version

```text
14.6.0
```

## V14.6 Meaning

V14.6 upgrades the product from a synchronous long-chain request into a three-system asynchronous station queue runtime.

Three systems:

```text
report import system
  -> task generation system
  -> task lifecycle system
```

Core rules:

- Report import APIs finish the import system only.
- Task generation is enqueued into `pipeline_jobs` and `station_queue`.
- A queue worker runs one station at a time: product snapshot, signal snapshot, signal pool, RAG, Agent, task snapshot, task pool.
- Agent and task materialization failures are isolated to station queue state; they no longer crash the upload request.
- Frontend receives `import completed + task generation queued`, then polls queue/gate status.
