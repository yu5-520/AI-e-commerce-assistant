Current Version: 16.3

V16.3 Current-Run Real Task Pool Acceptance

Core chain:

`Report schema Agent -> system cleaning -> fullProductBundle -> real product judgment Agent -> product_judgment_package 70% gate -> real task mapping Agent with RAG permissions/SOP -> current-run task-pool admission -> current-run frontend read model -> task-pool acceptance -> data metro line`

Key fix:

- V16.2 real product and task Agents remain unchanged.
- V16.3 adds a read-only acceptance gate for the current execution queue.
- `/api/view/task-pool-acceptance` compares latestRun, current task_pool_entries, frontend_task_view and frontend_task_detail_view.
- Data page task count must equal task pool current dataVersion count.
- Task pool current dataVersion count must equal task page visible count.
- Every visible task must have a detail projection.
- Old task_pool rows can remain as history, but old frontend_task_view rows are treated as pollution.
- If counts mismatch, data-line enters attention instead of pretending the chain is complete.

Boundary:

V16.3 does not generate, repair, or supplement tasks. It only validates that the real generated tasks are aligned across run snapshot, task pool, frontend task list and task detail view. No alignment means no MVP acceptance.
