# Current Version

```text
15.0
```

## V15 Meaning

V15 is the full-chain Agent Budget Ledger and Agent-specific LLM Gateway release.

Mainline:

```text
report upload / API import
  -> report schema Agent: headers / sheets / schema mapping only
  -> system code cleaning and fact ingestion
  -> fullProductBundle assembly
  -> product judgment Agent: product-bundle analysis and confidence judgments only
  -> system product_judgment_package compression and 70% confidence gate
  -> task mapping Agent: company RAG / permission RAG / SOP RAG mapping only
  -> system task-pool admission
  -> frontend read model refresh
  -> data page renders metro-line and full-chain Agent budget status
```

Core rules:

- Report Agent only creates `report_schema_mapping`; it never cleans rows, judges products, or creates tasks.
- Product judgment Agent only analyzes fullProductBundle, category, data changes, trend, comparison, baseline and confidence; it never creates tasks.
- System compresses product judgments by real `productId` into `product_judgment_package` and allows task mapping only when package confidence reaches 70%.
- Task mapping Agent only maps 70%+ judgment packages into permission-aware tasks using company permissions, account permissions, SOP and approval RAG.
- All Agent/API/RAG usage is recorded in `agent_budget_ledgers_v15` and `agent_call_events_v15`.
- API calls must not scale with report rows, metric judgments, or task count.
- Default run budget: report schema Agent 0-3 calls, product judgment Agent 0-3 calls, task mapping Agent 0-2 calls, total Agent calls <= 8.
- Fallback is mandatory: schema dictionary, local metric expansion, and permission SOP templates keep the chain running when API is not used.

一句话：V15 把 Agent 从“到处调用的大模型”收束成“有职责、有预算、有缓存、有降级、有权限边界的站点能力”。
