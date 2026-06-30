Current Version: 14.9

V14.9 Dual-Agent Product Judgment Package Pipeline

Core chain:

`Import -> product projection -> fullProductBundle -> RAG boundary -> Agent1 analysis -> product_judgment_package -> Agent2 task generation -> task-pool admission -> frontend read model -> data metro line`

Key updates:

- Agent1 analyzes fullProductBundle and writes raw metric/product judgments only.
- System integration compresses raw judgments into one product_judgment_package per product.
- Agent2 generates task decisions only from product_judgment_package.
- Task pool receives only admitted product-level SOP tasks.
- New runtime tables: `agent_product_judgments_v15`, `product_judgment_packages_v15`, `task_generation_decisions_v15`.
- Metro line now includes the integration station: 接入、建档、全量包、判断、整合、任务、展示.
- Judgment can be metric-level and detailed; tasks must be product-level and compressed.

Boundary:

Fixing Agent1 judgment quality must not affect task generation chain integrity. Fixing Agent2 SOP quality must not change raw product analysis. System package compression is the stable contract between them.
