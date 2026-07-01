# Current Version

```text
16.1
```

## V16.1 Meaning

V16.1 is the MVP-real product judgment Agent release.

It keeps the V15/V15.1 guardrails:

```text
- three-Agent budget ledger
- current-run dataVersion isolation
- no demo/seed task pollution
- product_judgment_package 70% confidence gate
```

Then it changes the product judgment stage from local/system rule expansion to a real batched Agent call:

```text
fullProductBundle batch
  -> real product judgment Agent API call
  -> strict JSON judgments
  -> system validation
  -> agent_product_judgments_v15
  -> product_judgment_packages_v15
  -> 70% package confidence gate
```

Core rules:

- Product judgment Agent must analyze batched fullProductBundle records through a real provider call.
- Default call unit is a product batch, not a row, metric, or task.
- Default batch size is 30 products and max product judgment calls per run is 3.
- API key is read from `PRODUCT_JUDGMENT_AGENT_API_KEY`, `DEEPSEEK_API_KEY`, or `LLM_API_KEY`.
- Provider URL/model can be configured with `PRODUCT_JUDGMENT_AGENT_BASE_URL` and `PRODUCT_JUDGMENT_AGENT_MODEL`.
- The Agent must return strict JSON with a top-level `judgments` array.
- The system validates returned `productId`, `storeId`, `metricCode`, `severity`, `confidence`, `decisionHint`, `finding`, and `evidence` before writing judgments.
- If API key is missing, provider call fails, JSON is invalid, or no valid judgments are returned, the pipeline records the failure and does not generate fake judgments or fake tasks.
- System code still owns package compression, 70% package confidence gate, task-pool admission, lifecycle state, and current-run frontend read model.
- Task mapping remains template/RAG-placeholder until V16.2; V16.1 only opens real product judgment Agent.

一句话：V16.1 让“商品有没有问题、问题有多可信”进入真实 Agent 判断阶段；失败宁可空链路，也不再用本地垫底判断冒充真实 Agent。
