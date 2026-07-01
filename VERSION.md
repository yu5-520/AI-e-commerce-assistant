# Current Version

```text
14.9.4
```

## V14.9.4 Meaning

V14.9.4 is the Agent1 API/RAG budget guard release.

It keeps the V14.9 dual-Agent mainline:

```text
report import system
  -> background worker compute
  -> system product layered snapshot
  -> fullProductBundle assembly
  -> RAG volatility boundary context
  -> Agent 1 budget-guarded metric expansion
  -> system real-product package gate
  -> Agent 2 task generation station
  -> system task-pool admission station
  -> frontend read model refresh
  -> data page renders current-run metro-line chain status
```

Fix scope:

- Agent1 can still expand one product bundle into many metric judgments.
- Metric judgment creation is local record expansion and must not trigger one LLM/API call per judgment.
- Agent1 API call count is product-bundle scoped and must be `<= inputBundleCount`.
- Current implementation sets Agent1 metric expansion to local deterministic mode: `agent1ApiCallCount = 0`.
- RAG context is reused by dataVersion/run and records `ragRetrievalCount`.
- Task generation run now records `agent1ApiCallCount`, `agent1ApiBudget`, `agent1ApiCallsPerBundle`, `ragRetrievalCount`, and `apiBudgetViolation`.
- Data-line shows API budget status beside judgment count.

Core rule:

`判断可以多，API调用必须少；一条判断不能等于一次API。`
