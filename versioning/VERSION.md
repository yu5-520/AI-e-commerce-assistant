Current Version: 14.9.1

V14.9.1 Dual-Agent Runtime Reset Boundary Fix

Core chain remains:

`Import -> product projection -> fullProductBundle -> RAG boundary -> Agent1 analysis -> product_judgment_package -> Agent2 task generation -> task-pool admission -> frontend read model -> data metro line`

Key fix:

- Demo reset now clears `task_generation_runs_v14`.
- Demo reset now clears `agent_product_judgments_v15`, `product_judgment_packages_v15`, and `task_generation_decisions_v15`.
- DB diagnostics now check V14/V15 residual runtime tables together.
- Data-line status ignores stale generation-run rows when upstream data is empty.
- Empty runtime should not show residual judgment counts.

Boundary:

Reset must clear all generated runtime artifacts while preserving accounts, roles, permissions, and base configuration. After reset, `fact source = 0` and V14/V15 runtime tables must also be 0.
