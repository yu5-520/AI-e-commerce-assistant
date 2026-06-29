# V14.3 Update Summary

## Theme

V14.3 upgrades the task-generation architecture from previous-snapshot comparison into a full product signal package system.

Core goal:

```text
system generates all product signal packages
RAG defines operation-value and budget boundaries
Agent judges packages in batches
budgeted task snapshots enter lifecycle immediately
```

## Mainline

```text
report import
  -> operating snapshot
  -> system product layered snapshot
  -> full product signal package snapshot
  -> signal package queue
  -> RAG operation-value context
  -> Agent budget judgment
  -> budgeted task snapshot
  -> task pool
  -> task lifecycle
```

## Product Snapshot Split

System product snapshot now has three internal layers:

```text
product profile snapshot
product metric snapshot
Agent product package seed
```

Product profile snapshot contains identity and category context:

```text
product id
SKU / SPU / ERP code
platform
store
product link
vertical category
category levels
price band
product role
lifecycle stage
hero/new/campaign flags
```

Product metric snapshot contains operating state:

```text
ROAS / ROI
ad spend
payment amount
gross margin
click rate
conversion rate
refund rate
inventory
sellable days
organic / paid visitors
```

## Full Signal Package

V14.3 no longer creates signals only for abnormal products.

Every product receives a signal package:

```text
normal_state
product_newly_seen
product_missing_from_latest
product_roas_changed
product_inventory_changed
product_refund_changed
product_conversion_changed
...
```

Normal products are not dropped. They are sent to Agent judgment as low-priority packages.

## Multi-window Trend Context

Signal packages include lightweight trend windows:

```text
previous
7d
30d
90d
```

The package carries latest value, historical average, window count and change-vs-average.

## Agent Batch Queue

Agent does not wait for all packages to finish.

```text
queue full signal packages
Agent judges at most 20 packages per batch
0-N task snapshots may be generated
new task snapshots immediately enter budget reservation and task pool
Agent continues judging next batch
```

## RAG Operation Value Layer

RAG must define operation-value boundaries, including:

```text
category baseline
ROAS action rule
SOP card
task creation boundary
task merge/cooldown rule
data-gap rule
store/product weight rule
budget rule
historical recap
```

Agent does not freely decide operation value without RAG context.

## Budgeted Task Generation

Agent-generated task plans now carry operation budget fields:

```text
operationBudget
estimatedBudgetCost
budgetFormula
budgetType
budgetStatus
riskLevel
operatorBudgetApplies
```

Budget estimation is supported for:

```text
ROAS increase
ROAS decrease
campaign apply
replenishment
title test
main image test
detail page test
after-sales check
data-gap fix
```

High-risk tasks go to manager review and do not consume ordinary operator budget.

## Runtime Counters

V14.3 responses should expose:

```text
productSnapshotCount
productSignalPackageCount
productSignalCount
signalCount
judgmentCount
taskSnapshotCount
createdTaskCount
observeOrNoiseCount
```

## Boundary

System responsibilities:

```text
full package generation
multi-window calculation
queueing
budget reservation
lifecycle state
permission control
```

RAG responsibilities:

```text
operation-value definition
SOP boundary
budget rule
merge/cooldown rule
historical recap
```

Agent responsibilities:

```text
judge package value
generate budgeted task plan
define SOP and evidence
choose task / observe / ignore / data-gap / manager-review
```
