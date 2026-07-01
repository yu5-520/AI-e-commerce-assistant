# Current Version

```text
14.9.1
```

## V14.9.1 Meaning

V14.9.1 is the runtime reset boundary fix for the V14.9 dual-Agent pipeline.

It keeps the V14.9 mainline:

```text
report import system
  -> background worker compute
  -> system product layered snapshot
  -> fullProductBundle assembly
  -> RAG volatility boundary context
  -> Agent 1 product analysis station
  -> system product_judgment_package integration station
  -> Agent 2 task generation station
  -> system task-pool admission station
  -> frontend read model refresh
  -> data page renders metro-line chain status
```

Fix scope:

- `reset-runtime-data` now clears `task_generation_runs_v14`.
- `reset-runtime-data` now clears V14.9 dual-Agent tables: `agent_product_judgments_v15`, `product_judgment_packages_v15`, and `task_generation_decisions_v15`.
- System diagnostics now include V14/V15 residual checks.
- Data-line view ignores stale generation-run rows when upstream data is empty.
- Empty runtime must show: 接入等待、建档等待、全量包等待、判断等待、整合等待、任务等待、展示等待.

Core rule:

`fact source = 0` means V14/V15 snapshots, judgments, judgment packages, task decisions, task generation runs, task pool, and frontend read models must also be 0.
