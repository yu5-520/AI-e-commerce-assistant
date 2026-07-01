# Current Version

```text
15.1
```

## V15.1 Meaning

V15.1 is the current-run isolation and no-demo-pollution release.

It keeps the V15 three-Agent budget ledger, then adds two hard gates:

```text
1. Product judgments are data-change driven.
   Agent1 no longer pads every product to a fixed 8-metric judgment set.
   Judgment count follows fullProductBundle.fieldSignals, abnormal metrics and critical data gaps.

2. Frontend task queue is current-run isolated.
   Task page reads only latestRun.dataVersion.
   Old demo / seed / global task_pool entries cannot pollute the current execution queue.
```

Mainline:

```text
report upload / API import
  -> report schema Agent: headers / sheets / schema mapping only
  -> system code cleaning and fact ingestion
  -> fullProductBundle assembly
  -> product judgment Agent: only changed/abnormal/data-gap metrics become judgments
  -> system product_judgment_package compression and 70% confidence gate
  -> task mapping Agent: company RAG / permission RAG / SOP RAG mapping only
  -> system task-pool admission
  -> frontend read model refresh by latestRun.dataVersion
  -> data page and task page show the same current-run task count
```

Core rules:

- Report Agent only creates `report_schema_mapping`; it never cleans rows, judges products, or creates tasks.
- Product judgment Agent only analyzes fullProductBundle, category, data changes, trend, comparison, baseline and confidence; it never creates tasks.
- Agent1 metric judgments must be driven by changed/abnormal metrics or data gaps, not by a fixed metric list.
- System compresses product judgments by real `productId` into `product_judgment_package` and allows task mapping only when package confidence reaches 70%.
- Task mapping Agent only maps 70%+ judgment packages into permission-aware tasks using company permissions, account permissions, SOP and approval RAG.
- `/api/view/tasks` reads the latest run dataVersion by default.
- `frontend_task_view` is rebuilt from `task_pool_entries WHERE data_version = latestRun.dataVersion`.
- Old demo, seed, fallback, and history tasks can remain in storage but must not enter the current execution queue.
- All Agent/API/RAG usage is recorded in `agent_budget_ledgers_v15` and `agent_call_events_v15`.
- API calls must not scale with report rows, metric judgments, or task count.

一句话：V15.1 把“数据真实参与”和“本轮任务隔离”补上，避免系统规则垫底和旧 DEMO 任务把真实导入链路搅乱。
