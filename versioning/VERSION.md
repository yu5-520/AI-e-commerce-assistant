Current Version: 14.9.4

V14.9.4 Agent1 API/RAG Budget Guard

Core chain:

`Import -> product projection -> fullProductBundle -> RAG boundary -> Agent1 budget-guarded metric expansion -> real-product package gate -> Agent2 task generation -> task-pool admission -> frontend read model -> data metro line`

Key fix:

- Agent1 can expand one resolved fullProductBundle into multiple metric-level judgments.
- Metric judgments are local records and must not each call DeepSeek/LLM.
- Agent1 API call count is product-bundle scoped and must be less than or equal to input bundle count.
- Current Agent1 metric expansion is deterministic/local: `agent1ApiCallCount = 0`.
- RAG context is reused by dataVersion/run and records `ragRetrievalCount`.
- Data-line and task generation run now expose API budget counters.

Boundary:

Judgment may be detailed and metric-level. API/RAG calls must remain product-bundle or dataVersion scoped. Formal tasks must be product-level and counted by current run, not by global task pool.
