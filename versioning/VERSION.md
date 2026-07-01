Current Version: 16.2

V16.2 Real Task Mapping Agent + RAG MVP

Core chain:

`Report schema Agent -> system cleaning -> fullProductBundle -> real batched product judgment Agent -> strict JSON judgment validation -> product_judgment_package 70% gate -> real task mapping Agent with RAG permissions/SOP -> strict JSON task validation -> current-run task-pool admission -> current-run frontend read model -> data metro line`

Key fix:

- Product judgment remains real and batched from V16.1.
- 70%+ product judgment packages now go into a real task mapping Agent instead of local SOP templates.
- Task mapping Agent uses RAG permission/SOP/approval/evidence context.
- Returned JSON must contain a `tasks` array and must pass system validation.
- Formal tasks must have at least 3 SOP steps and 2 evidence requirements.
- Missing API key, provider failure, invalid JSON, or zero valid tasks does not fall back to template tasks.
- Default task mapping budget: 8 packages per call, max 2 calls per run.
- Provider configuration uses `TASK_MAPPING_AGENT_API_KEY` / `DEEPSEEK_API_KEY`, plus optional `TASK_MAPPING_AGENT_BASE_URL` and `TASK_MAPPING_AGENT_MODEL`.
- System still owns package merging, task-pool admission, same-product dedupe, lifecycle state and current-run filtering.

Boundary:

Agent is real for product judgment and task mapping. Code owns cleaning, calculations, package merging, validation, current-run filtering and lifecycle state. No valid real Agent task output means no fake task.
