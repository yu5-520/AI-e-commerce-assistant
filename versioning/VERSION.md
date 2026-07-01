Current Version: 16.1

V16.1 Real Product Judgment Agent MVP

Core chain:

`Report schema Agent -> system cleaning -> fullProductBundle -> real batched product judgment Agent -> strict JSON validation -> product_judgment_package 70% gate -> task mapping template until V16.2 -> current-run task-pool admission -> current-run frontend read model -> data metro line`

Key fix:

- Product judgment stage now calls a real LLM provider in product batches.
- Returned JSON must contain a `judgments` array and must pass system validation.
- Missing API key, provider failure, invalid JSON, or zero valid judgments does not fall back to fake/local judgments.
- Default product judgment budget: 30 products per call, max 3 calls per run.
- Provider configuration uses `PRODUCT_JUDGMENT_AGENT_API_KEY` / `DEEPSEEK_API_KEY`, plus optional `PRODUCT_JUDGMENT_AGENT_BASE_URL` and `PRODUCT_JUDGMENT_AGENT_MODEL`.
- System still owns package merging, 70% confidence gate, task-pool admission and current-run filtering.
- Task mapping remains template-based until V16.2 real permission/RAG task Agent.

Boundary:

Agent is now real for product judgment only. Code owns cleaning, calculations, package merging, current-run filtering, task lifecycle and failure transparency. No real Agent output means no fake task.
