# Current Version

```text
14.6.1
```

## V14.6.1 Meaning

V14.6.1 adds automatic station queue consumption.

Mainline:

```text
report import system
  -> enqueue task generation
  -> background station queue worker
  -> task lifecycle system
```

Core rules:

- FastAPI startup starts a conservative background `station_queue` worker.
- The worker runs outside upload requests and consumes a small bounded number of stations per tick.
- Pipeline API exposes worker status, start, stop, and one-tick controls.
- Manual batch execution remains available for debugging.
- Upload requests still finish after import and enqueue; they do not wait for Agent or task materialization.
