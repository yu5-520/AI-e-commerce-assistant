Current Version: 15.0

V15 Full-Chain Agent Budget Ledger + Agent Gateway

Core chain:

`Report schema Agent -> system cleaning -> fullProductBundle -> product judgment Agent -> product_judgment_package 70% gate -> task mapping Agent with permission/SOP RAG -> task-pool admission -> frontend read model -> data metro line`

Key fix:

- Report Agent only translates headers/sheets into system schema mapping.
- Product judgment Agent analyzes product bundles, trends, comparison, category and confidence, then system merges judgments into product packages.
- Product packages only enter task mapping when system-computed package confidence reaches 70%.
- Task mapping Agent retrieves company permissions, account permissions, approval rules and SOP RAG before creating tasks.
- All three Agent stages share `agent_budget_ledgers_v15` and `agent_call_events_v15`.
- API calls must stay within the run budget and must not scale with rows, metrics, or tasks.

Boundary:

Agent is a budgeted station capability, not a per-row worker. Code owns cleaning, calculations, package merging, task-pool admission and lifecycle state.
