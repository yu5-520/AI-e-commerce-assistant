# Current Version

```text
14.9.3
```

## V14.9.3 Meaning

V14.9.3 is the Agent1 metric-expansion and product-package compression release.

It keeps the V14.9 dual-Agent mainline:

```text
report import system
  -> background worker compute
  -> system product layered snapshot
  -> fullProductBundle assembly
  -> RAG volatility boundary context
  -> Agent 1 metric-level analysis expansion
  -> system real-product package gate
  -> Agent 2 task generation station
  -> system task-pool admission station
  -> frontend read model refresh
  -> data page renders current-run metro-line chain status
```

Fix scope:

- Agent1 no longer emits only one judgment per product signal.
- A resolved fullProductBundle is expanded into multiple metric-level judgments, such as ROI, refundRate, inventory, conversionRate, grossMargin, adSpend, and paymentAmount.
- Product identity gaps still stay in Agent1 and cannot enter Agent2.
- The package integration station still compresses by real `productId`, so many metric judgments become one `product_judgment_package` per product.
- Agent2 still only consumes the compressed product package and task-pool admission remains capped, product-level, and duplicate-safe.
- Data-line now records `averageJudgmentsPerBundle` and keeps formal task count on latest run `taskPoolCreatedCount`.

Core rule:

`Agent1 判断要细，整合站必须压回商品级，任务数必须看本轮产出。`
