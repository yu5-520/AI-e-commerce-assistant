# Current Version

```text
16.2
```

## V16.2 Meaning

V16.2 is the MVP-real task mapping Agent + RAG release.

It keeps the V16.1 real product judgment Agent, then opens the next real stage:

```text
fullProductBundle
  -> real product judgment Agent API call
  -> strict JSON judgments
  -> product_judgment_package + 70% confidence gate
  -> real task mapping Agent API call with RAG permission/SOP context
  -> strict JSON tasks
  -> system validation
  -> task snapshots / task pool / current-run read model
```

Core rules:

- Product judgment Agent remains real and batched.
- Task mapping Agent only receives `product_judgment_package` rows whose `packageConfidence >= 0.70`.
- Task mapping Agent must use RAG context: company permissions, account permissions, approval rules, SOP, evidence requirements and review metrics.
- Task mapping output must be strict JSON with a top-level `tasks` array.
- Each formal task must include `packageId`, `productId`, `storeId`, `decision`, `taskTitle`, `priority`, `deadline`, `assigneeRole`, `approvalRequired`, `forbiddenActions`, `sopSteps`, `evidenceRequirements`, `reviewMetrics`, and `reason`.
- A formal task must have at least 3 SOP steps and at least 2 evidence requirements.
- System validates every task against the current candidate package before writing `task_generation_decisions_v15`.
- Missing API key, provider failure, invalid JSON, or zero valid task output creates no fake task and no local SOP-template fallback.
- System code still owns task-pool admission, same-product dedupe, lifecycle state and current-run frontend read model.

一句话：V16.2 让“该让谁做、按什么权限做、提交什么证据、如何复盘”进入真实 RAG 任务映射 Agent；失败宁可无任务，也不再用模板任务冒充真实 Agent。
