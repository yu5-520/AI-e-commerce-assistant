Current Version: 14.8.2

V14.8.2 Product Data Date + Mature Task Queue

Core chain:

`Import -> product projection -> fullProductBundle -> RAG boundary -> Agent soft routing -> mature/severe-gap task snapshot -> task pool -> frontend read model`

Key updates:

- Product metric facts show business data date such as `2026.6.25`, not cache/read-model/projection labels.
- Report date resolution uses report fields first, filename/dataVersion second, upload/create time third.
- Agent deterministic routing is the only authority for entering the formal task pool.
- LLM can enrich wording but cannot upgrade background observation into a formal task.
- Observation items stay in labels/logs; mature经营判断 and severe数据缺口 enter SOP task snapshots.
- Frontend task read model exposes `id = taskId`, so list detail and task report use one key.
- Read-model refresh clears stale task rows before rebuilding visible queue rows.

Boundary:

Read APIs stay read-only. Compute happens in worker/stations. Observation is not execution; task pool only holds actionable SOP tasks.
