Current Version: 14.8.3

V14.8.3 Station Chain Contract + Metro Line UI

Core chain:

`Import -> product projection -> fullProductBundle -> RAG boundary -> Agent soft routing -> task_generation_run -> optional task pool -> frontend read model -> data metro line`

Key updates:

- Task generation is now a stable run contract. Even if Agent produces zero formal tasks, the run is recorded as completed.
- `task_generation_runs_v14` records input bundles, Agent judgments, formal task count, observe-only count, task-pool created count, and reason.
- Data page sync summary is replaced with a metro-line station UI: 接入、建档、全量包、判断、任务、展示.
- Main page hides engineering sync strings such as `同步：总览 / 经营 / 任务 / 数据 / 日志`.
- `GET /api/view/data-line` returns a read-only product-facing chain status object.
- Observe-only is a valid station result; it does not enter `task_pool`, but it still proves the chain completed.

Boundary:

Agent task strategy can change later without breaking the chain contract. Frontend shows pipeline state separately from formal task count.
