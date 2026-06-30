# Current Version

```text
14.8.2
```

## V14.8.2 Meaning

V14.8.2 is a task-quality and detail-page repair over V14.8.1.

Mainline:

```text
report import system
  -> background worker compute
  -> system product layered snapshot
  -> fullProductBundle assembly
  -> RAG volatility boundary context
  -> Agent product diagnosis soft routing
  -> only mature judgment / severe data gap creates V11.8 SOP task snapshot
  -> observe-only and background observation stay out of formal task pool
  -> taskId becomes the unified frontend detail key
  -> frontend read model refresh
```

Core rules:

- Product metric cards display business data date, for example `2026.6.25`, not engineering labels such as cache/read model/projection.
- Report date priority: report field date first, filename/dataVersion date second, upload/create date third.
- LLM may enrich Agent wording, but it may not upgrade `observe_only` into a task-pool entry.
- Only mature operating judgments and serious data gaps enter `task_snapshot -> task_pool`.
- Background observation is filtered out of the execution queue.
- Task read model must expose `id = taskId` so list cards and detail pages use the same key.
- Detail fallback remains backend-driven; frontend should not depend on local transient state only.
