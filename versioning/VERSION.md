Current Version: 14.9.3

V14.9.3 Agent1 Metric Expansion + Product Package Compression

Core chain:

`Import -> product projection -> fullProductBundle -> RAG boundary -> Agent1 metric expansion -> real-product package gate -> Agent2 task generation -> task-pool admission -> frontend read model -> data metro line`

Key fix:

- Agent1 expands one resolved fullProductBundle into multiple metric-level judgments.
- The metric judgment layer can now be larger than the product package layer.
- Product package integration still uses real `productId` only.
- Missing product identity is recorded as a judgment gap and cannot enter Agent2 task generation.
- Agent2 only consumes compressed `product_judgment_package` rows.
- Data-line formal task count still shows latest run `taskPoolCreatedCount`, while global task-pool total is reported separately.

Boundary:

Agent1 judgment may be detailed and metric-level. Integration must compress those judgments back to one package per real product. Formal tasks must be product-level and counted by current run, not by global task pool.
