Current Version: 15.1

V15.1 Current-Run Isolation + No-Padding Product Judgment

Core chain:

`Report schema Agent -> system cleaning -> fullProductBundle -> data-change product judgment Agent -> product_judgment_package 70% gate -> task mapping Agent with permission/SOP RAG -> current-run task-pool admission -> current-run frontend read model -> data metro line`

Key fix:

- Product judgment count is no longer padded to a fixed 8 metrics per product.
- Agent1 expands only changed, abnormal, or critical data-gap metrics from fullProductBundle.fieldSignals.
- Task page reads only latestRun.dataVersion by default.
- `frontend_task_view` is rebuilt from current dataVersion task_pool entries only.
- Old demo, seed, fallback, and historical tasks are blocked from the current execution queue.
- Data page and task page should now align on current-run task count.
- All three Agent stages still share `agent_budget_ledgers_v15` and `agent_call_events_v15`.

Boundary:

Agent is a budgeted station capability, not a per-row worker. Code owns cleaning, calculations, package merging, task-pool admission, current-run filtering, and lifecycle state.
