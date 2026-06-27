# API_CONTRACT

本文件只记录当前前端和当前主架构会使用的真实 API。历史接口不进入本文件；无法在 FastAPI app 中解析到的接口不得写入本文件。

## 账号

```text
GET  /api/accounts
GET  /api/accounts/me
POST /api/accounts/switch
GET  /api/accounts/users
GET  /api/accounts/users/{user_id}
POST /api/accounts/users/{user_id}/role
POST /api/accounts/users/{user_id}/stores
GET  /api/accounts/store-assignments
GET  /api/accounts/store-migrations
POST /api/accounts/store-assignments/{store_id}
GET  /api/accounts/roles
POST /api/accounts/roles/{role_id}/permissions
GET  /api/accounts/permissions
GET  /api/accounts/store-groups
GET  /api/accounts/stores
GET  /api/accounts/role-change-logs
```

用途：账号切换、角色权限、店铺归属、老板 / 总管 / 运营视图。ECS Demo 允许通过 `DEMO_ACCOUNT_SWITCH=true` 显式开启账号切换；前端必须先通过后端验证再写 localStorage。

## 模块

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

## 数据导入

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
GET    /api/data/alerts/events
GET    /api/data/versions
GET    /api/data/latest-version
```

边界：`/api/data/upload/*` 只负责文件解析、Sheet/Block 识别、字段读取、经营对象同步、指标事实入库、数据缺口留痕和布局诊断；不得提前写死经营建议。任务只能由趋势/经营信号触发，并经过证据闸门。

导入结果必须携带或同步生成：

```text
operating_products / operating_stores 身份主档
product_metric_facts / store_metric_facts / traffic_source_facts 独立事实表
data_gap_events 数据缺口池
importDiagnostics：layoutMode / stageTrace / sheets[].blocks[]
business_signals_v6 业务信号
evidenceGateSync 任务证据闸门结果
v116 闭环反查结果
```

importDiagnostics 验收重点：

```text
layoutMode = sheet_block_fact_gap_staging
stageTrace = Sheet → Block → Fact → Gap → Staging → EvidenceGate
sheets[].blocks[].targetTable
sheets[].blocks[].metricScope
sheets[].blocks[].factCount / gapCount / staging
acceptance.status
```

## 任务

```text
GET  /api/modules/todo
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
POST /api/modules/todo/{task_id}/complete
POST /api/modules/todo/reset
```

V12.3 边界：任务栏只承接高风险 / 高时效 / 需要人工执行的事项。任务生成必须先来自经营判断，再由 `task_evidence_gate_service` 检查关键证据。证据闸门必须返回 `metricScope / requiredFactTables / forbiddenCrossScope`，禁止跨口径取 ROI。缺关键证据时降级为“经营证据补齐任务”。

## 任务详情 / 报告

```text
GET /api/modules/task-reports/tasks/{task_id}
GET /api/modules/task-reports/candidates/{module}/{id}
GET /api/modules/task-reports/alerts/{id}
```

用途：解释为什么预警、怎么处理、需要什么证据。任务进入执行队列后，详情页必须可打开。

## 趋势

```text
GET  /api/trends/summary
POST /api/trends/metric-evidence
POST /api/trends/task-sop
```

趋势信号可以完整保留，但任务进入待办前必须经过证据闸门；普通缺口不得直接生成任务；ROI 必须按 product / traffic_source / store 口径取证。

## LLM / Agent

```text
GET  /api/llm/status
POST /api/llm/generate
GET  /api/llm/traces
GET  /api/llm/tools
GET  /api/llm/tools/{tool_name}
GET  /api/llm/mcp
```

LLM / Agent 只增强报表布局识别、判断说明、标签、报告和任务草案，不直接执行真实经营动作。

## 系统

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

清空运行态必须删除：

```text
workflow_runs
execution_logs
import_records
approval_records
task_status
task_assignments
task_submissions
task_reviews
report_records
data_snapshots
metric_snapshots
business_signals_v6
alert_events
imported_report_rows
operating_products
operating_stores
product_metric_facts
store_metric_facts
traffic_source_facts
data_gap_events
```

## 架构验收

```text
GET /api/architecture/v10/task-driven-product
GET /api/architecture/v10/readiness
```

V12.3 MVP 验收以真实报表导入后的经营对象、指标事实、缺口池、布局诊断、证据闸门、队列、详情页、账号切换和数据源契约稳定性为主。
