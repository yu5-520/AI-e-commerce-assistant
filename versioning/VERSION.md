Current Version: 14.9.2

V14.9.2 Real Product Package Gate + Current-Run Count

Core chain:

`Import -> product projection -> fullProductBundle -> RAG boundary -> Agent1 analysis -> real-product package gate -> Agent2 task generation -> task-pool admission -> frontend read model -> data metro line`

Key fix:

- Product package integration must use real `productId` only.
- `entityId`, `bundleId`, `signalId`, `SKU`, `SPU`, `LINK`, and other engineering IDs cannot become product package IDs.
- Missing product identity is recorded as a judgment gap and cannot enter Agent2 task generation.
- Agent2 only consumes resolved `product_judgment_package` rows.
- Same product in the same data version is checked before task-pool admission to prevent duplicate product tasks.
- Data-line formal task count now shows latest run `taskPoolCreatedCount`, while global task-pool total is reported separately.

Boundary:

Judgment may remain metric-level and detailed. Integration must compress by real product. Formal tasks must be product-level and counted by current run, not by global task pool.
