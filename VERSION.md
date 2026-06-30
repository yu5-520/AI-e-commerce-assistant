# Current Version

```text
14.9
```

## V14.9 Meaning

V14.9 is the dual-Agent station split and product judgment package compression release.

Mainline:

```text
report import system
  -> background worker compute
  -> system product layered snapshot
  -> fullProductBundle assembly
  -> RAG volatility boundary context
  -> Agent 1 product analysis station
  -> system product_judgment_package integration station
  -> Agent 2 task generation station
  -> system task-pool admission station
  -> frontend read model refresh
  -> data page renders metro-line chain status
```

Core rules:

- Agent 1 only creates metric-level/product-level analysis judgments. It cannot create tasks, SOPs, or task-pool entries.
- The system compresses judgments by `dataVersion + storeId + productId` into `product_judgment_packages_v15`.
- Agent 2 only consumes `product_judgment_package` and creates product-level SOP task decisions.
- Task pool only accepts system-admitted product-level decisions.
- One product package creates at most one formal operating task in a run; extra indicators must be merged into the same product-level SOP.
- Data page metro line is now: 接入 / 建档 / 全量包 / 判断 / 整合 / 任务 / 展示.
- Judgment count can be high; task count must be controlled.
- V14.8.3 chain contract remains: zero formal tasks can still be a completed chain result.
