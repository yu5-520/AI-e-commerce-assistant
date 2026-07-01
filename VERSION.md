# Current Version

```text
14.9.2
```

## V14.9.2 Meaning

V14.9.2 is the real-product package hard gate and current-run task count fix.

It keeps the V14.9 dual-Agent mainline:

```text
report import system
  -> background worker compute
  -> system product layered snapshot
  -> fullProductBundle assembly
  -> RAG volatility boundary context
  -> Agent 1 product analysis station
  -> system real-product package gate
  -> Agent 2 task generation station
  -> system task-pool admission station
  -> frontend read model refresh
  -> data page renders current-run metro-line chain status
```

Fix scope:

- Package integration can no longer fall back to `entityId`, `bundleId`, `signalId`, `SKU`, `SPU`, `LINK`, or other engineering IDs.
- Only a resolved real `productId` can become a `product_judgment_package`.
- Product identity gaps stay as Agent1 judgments and cannot enter Agent2 task generation.
- Package admission is stricter: medium risk needs multiple signals or stronger evidence; high/critical risk still enters.
- Agent2 task generation is capped per run and checks same-product task-pool duplicates before creating a new task.
- Data-line formal task count now uses the latest run's `taskPoolCreatedCount`, not the global `task_pool_entries` total.

Core rule:

`判断可以细，整合必须按真实商品压缩，任务数必须看本轮产出。`
