# API_CONTRACT

本文件只记录 **V12.8.1 当前前端和当前主架构会使用的真实 API**。历史接口不进入本文件；无法在 FastAPI app 中解析到的接口不得写入本文件。

## 1. 账号

```text
GET  /api/accounts
GET  /api/accounts/me
POST /api/accounts/switch
GET  /api/accounts/users
GET  /api/accounts/users/{user_id}
POST /api/accounts/users/{user_id}/role
POST /api/accounts/users/{user_id}/stores
GET  /api/accounts/store-assignments
POST /api/accounts/store-assignments/{store_id}
GET  /api/accounts/roles
POST /api/accounts/roles/{role_id}/permissions
GET  /api/accounts/permissions
GET  /api/accounts/stores
GET  /api/accounts/role-change-logs
```

账号切换必须先经过后端验证，再写入前端 localStorage。ECS Demo 通过 `DEMO_ACCOUNT_SWITCH=true` 显式开启模拟账号切换。

## 2. 经营模块

```text
GET /api/modules/dashboard
GET /api/modules/operating-unit
GET /api/modules/product
GET /api/modules/product?storeId={store_id}
GET /api/modules/product?storeName={store_name}
GET /api/modules/product/{product_id}
GET /api/modules/competitor
GET /api/modules/listing
GET /api/modules/traffic
GET /api/modules/report
GET /api/modules/log
GET /api/modules/recap-candidates
```

商品模块规则：

```text
商品列表必须返回 objectId / archiveId / productId / storeId / storeName。
前端唯一档案 ID 使用 objectId / archiveId，不使用裸 productId。
商品详情必须包含 productPosition / metricSections / trafficSourceFacts / taskHistorySummary / metricFactSummary。
商品整体指标只读 product_metric_facts。
流量来源指标只读 traffic_source_facts。
店铺指标只读 store_metric_facts。
事实表未命中显示“未识别”，不能显示 0，不能读对象缓存。
```

## 3. 数据导入

```text
GET    /api/data/sources
GET    /api/data/source-connections
POST   /api/data/source-connections/{source_id}/sync
POST   /api/data/validate
POST   /api/data/import/mock
GET    /api/data/imports
GET    /api/data/import-records
GET    /api/data/metric-facts/summary
GET    /api/data/data-gaps/summary
GET    /api/data/import-diagnostics
GET    /api/data/import-diagnostics?dataVersion={data_version}
GET    /api/data/versions/{data_version}/detail
POST   /api/data/versions/{data_version}/rollback
DELETE /api/data/versions/{data_version}?confirm=true
GET    /api/data/templates
POST   /api/data/upload/preview
POST   /api/data/upload/confirm
POST   /api/data/preview
POST   /api/data/import/confirm
POST   /api/data/import/report
POST   /api/data/import/mock-alerts
GET    /api/data/v3-summary
GET    /api/data/alerts
GET    /api/data/versions
GET    /api/data/latest-version
```

边界：`/api/data/upload/*` 只负责文件解析、Sheet/Block 识别、字段读取、经营对象同步、指标事实入库、数据缺口留痕和布局诊断；不得提前写死经营建议。任务只能由趋势/经营信号触发，并经过证据闸门、RAG记忆、动作估算、权重置信度和权限闸门。

导入结果必须携带或同步生成：

```text
operating_products / operating_stores 身份主档
product_metric_facts / store_metric_facts / traffic_source_facts 独立事实表
data_gap_events 数据缺口池
importDiagnostics：layoutMode / stageTrace / sheets[].blocks[]
business_signals_v6 业务信号
evidenceGateSync 任务证据闸门结果
riskTaskSync：V12.8.1 生命周期任务同步结果
```

## 4. 任务生命周期

```text
GET  /api/modules/todo
GET  /api/modules/todo/lifecycle/summary
GET  /api/modules/todo/events
GET  /api/modules/todo/counters
GET  /api/modules/todo/{task_id}/evidence
POST /api/modules/todo/{task_id}/split
POST /api/modules/todo/{task_id}/assign
POST /api/modules/todo/{task_id}/accept
POST /api/modules/todo/{task_id}/submit
POST /api/modules/todo/{task_id}/submit-evidence
POST /api/modules/todo/{task_id}/review
POST /api/modules/todo/{task_id}/review-evidence
POST /api/modules/todo/{task_id}/recap
POST /api/modules/todo/{task_id}/recap/complete
POST /api/modules/todo/{task_id}/complete
POST /api/modules/todo/reset
```

V12.8.1 任务契约：

```text
/api/modules/todo 返回后端真实聚合任务，前端不得二次聚合。
每个可见任务必须带 taskLifecycle / lifecycleStage / lifecycleVersion。
接收后 stage = accepted。
提交材料后 stage = evidence_submitted。
主管复核通过后 stage = recap_scheduled，并写入 recapCycles。
recap/complete 后写入 autoRecapResult 和 ragCandidate。
pending_review 的 RAG 候选不能直接参与下一次任务生成。
approved + effective 的经验卡才能被 rag_business_memory_service 召回。
```

## 5. 任务详情 / 报告

```text
GET /api/modules/task-reports/tasks/{task_id}
GET /api/modules/task-reports/candidates/{module}/{id}
GET /api/modules/task-reports/alerts/{id}
```

用途：解释为什么预警、怎么处理、需要什么证据、当前生命周期阶段、自动复盘周期和RAG候选状态。任务进入执行队列后，详情页必须可打开；详情生成异常时必须 fail-closed 返回结构化报告，不能让页面 500。

## 6. RAG 经验库

```text
GET  /api/modules/rag-memory
GET  /api/modules/rag-memory/cases
GET  /api/modules/rag-memory/search
POST /api/modules/rag-memory/feedback/tasks/{task_id}
POST /api/modules/rag-memory/cases/{case_id}/approve
POST /api/modules/rag-memory/cases/{case_id}/reject
```

RAG 边界：复盘完成后先进入候选；只有 owner / manager 审核通过的 `approved` 且 `effective=true` 经验卡，才允许增强后续任务生成。

## 7. 趋势

```text
GET  /api/trends/summary
POST /api/trends/metric-evidence
POST /api/trends/task-sop
```

趋势信号可以完整保留，但任务进入待办前必须经过证据闸门；普通缺口不得直接生成任务；ROI 必须按 product / traffic_source / store 口径取证。

## 8. LLM / Agent

```text
GET  /api/llm/status
POST /api/llm/generate
GET  /api/llm/traces
GET  /api/llm/tools
GET  /api/llm/tools/{tool_name}
GET  /api/llm/mcp
GET  /api/modules/agents
GET  /api/modules/agents/{module}/{entity_id}
POST /api/modules/agents/{module}/{entity_id}/tasks
GET  /api/modules/agents/tasks/{task_id}/playbook
POST /api/modules/agents/tasks/generate
```

LLM / Agent 只增强报表布局识别、判断说明、标签、报告和任务草案，不直接执行真实经营动作。

## 9. 系统

```text
GET  /api/health
GET  /api/system/db-status
GET  /api/system/runtime-diagnostics
GET  /api/system/security
GET  /api/system/isolation
GET  /api/system/repositories
GET  /api/system/repositories?check=true
GET  /api/system/postgres-cutover-check
POST /api/system/backfill-operating-objects
POST /api/system/reset-runtime-data?confirm=true
POST /api/system/clear-runtime-data?confirm=true
POST /api/system/clear-demo-data?confirm=true
POST /api/system/reset-legacy-runtime-once
```

清空运行态必须删除数据导入、事实表、缺口池、信号、任务、复盘候选和日志等演示派生数据；账号、角色、权限、基础店铺配置必须保留。

## 10. 架构验收

```text
GET /api/architecture/v10/task-driven-product
GET /api/architecture/v10/readiness
```

V12.8.1 MVP 验收以真实报表导入后的经营对象、指标事实、缺口池、布局诊断、证据闸门、真实聚合任务队列、生命周期、自动复盘、RAG候选、账号切换和数据源契约稳定性为主。
