# Current Version

```text
14.7.0
```

## V14.7 Meaning

V14.7 corrects the task generation grain from fragmented metric/dataVersion signals to one full product bundle per product.

Mainline:

```text
report import system
  -> system product layered snapshot
  -> fullProductBundle assembly
  -> fullProductBundle queue
  -> RAG volatility boundary context
  -> Agent product diagnosis soft routing
  -> V11.8 SOP task snapshot when route is create_task / manager_review
  -> task pool
  -> task lifecycle system
```

Core rules:

- `fullProductBundle` is not a fourth fact layer. It is the contract that combines product profile layer, product data layer and product snapshot layer for Agent input.
- Signals are evidence inside the product bundle, not independent task entry points.
- RAG provides volatility boundary and operating context; it does not hard-block Agent.
- Agent soft routing can return create task, manager review, observe, merge, evidence-only or data-gap routes.
- Only create task / manager review routes become formal V11.8 SOP task snapshots.
- Missing fields lower confidence and request evidence; missing ROI or impact estimate does not automatically become manager approval.
- The formal task output remains the repository SOP package: taskCard, taskDetailReport, evidencePack, sopSteps, reviewMetrics, completionGate, failureThreshold, agentJudgment and ownership.
