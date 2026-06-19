# V4 Module Agent Runtime

V4 adds a module-level Agent layer to the AI ERP Operating Advisor MVP.

The product rule is simple:

```text
Agent 不放在最高控制位，而是放进各模块做增强。
```

## 1. Agent position

```text
ERP / CRM / Report data
↓
Module data and warning candidates
↓
V4 Module Agent
↓
Advisory analysis / summary / task drafts
↓
Human confirmation
↓
Unified task pool
↓
Operator execution / manager review / log archive
```

The Agent layer does not replace the task system. It produces structured material that the existing task system can accept after human confirmation.

## 2. Current Agent set

```text
竞品数据收集分析 Agent
上新标题 / 主图方案多样生成 Agent
售后归因 Agent
流量复盘 Agent
报表摘要 Agent
任务拆解 Agent
日报 / 周报 Agent
```

## 3. API

```text
GET  /api/modules/agents
GET  /api/modules/agents/{module}/{entity_id}
POST /api/modules/agents/{module}/{entity_id}/tasks
GET  /api/modules/agents/cycle/{target}
```

Supported module values:

```text
product
competitor
listing
traffic
report
task
```

## 4. Output contract

Every module Agent returns the same major fields:

```text
agentId
agentName
agentVersion
mode
sourceModule
sourceRoute
module
entityType
entityId
generatedAt
viewer
inputSnapshot
riskLevel
summary
evidence
suggestions
taskDrafts
humanDecision
forbiddenActions
boundary
nextStep
```

The `taskDrafts` field is the bridge into the unified task pool. It is a draft until the user clicks to create it.

## 5. Safety boundary

Agent can:

```text
generate suggestions
generate summaries
generate task drafts
generate title / main-image directions
generate daily / weekly recap structure
```

Agent cannot:

```text
directly change price
directly change ad spend
directly refund
directly publish or delist products
directly write to real ERP / CRM / marketplace data
```

## 6. Production upgrade path

Current V4 is a rules-based / mock-data Agent-ready layer. The next upgrade can plug an LLM into `src/services/module_agent_service.py` while keeping the same API contract.

Recommended next production steps:

```text
1. Add provider adapter: DeepSeek / OpenAI / internal model.
2. Add prompt templates per module.
3. Add RAG retrieval for ERP / CRM row-level evidence.
4. Add immutable Agent output logs.
5. Add owner / manager approval for high-impact Agent drafts.
6. Add evals for hallucination, missing evidence, and forbidden-action leakage.
```
