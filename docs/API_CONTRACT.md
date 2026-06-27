# API_CONTRACT

本文件只记录当前前端和当前主架构会使用的真实 API。历史接口不进入本文件。

## 账号

```text
GET  /api/accounts
GET  /api/accounts/me
POST /api/accounts/switch
GET  /api/accounts/users
POST /api/accounts/users/{user_id}/role
POST /api/accounts/users/{user_id}/stores
GET  /api/accounts/store-assignments
POST /api/accounts/store-assignments/{store_id}
GET  /api/accounts/roles
POST /api/accounts/roles/{role_id}/permissions
```

用途：账号切换、角色权限、店铺归属、老板 / 总管 / 运营视图。

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

用途：总览、经营、商品、店铺商品档案、单商品事实详情、竞品、上新、流量、数据、日志页面数据。

商品模块规则：

```text
不带参数 → 当前账号可见全局商品档案。
带 storeId / storeName → 当前店铺商品档案。
商品列表必须返回 objectId / archiveId / productId / storeId / storeName。
前端唯一档案 ID 使用 objectId / archiveId，不使用裸 productId。
商品详情必须包含 productPosition / metricSections / trafficSourceFacts / taskHistorySummary / metricFactSummary。
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

用途：执行队列、证据提交、总管复核、任务完成。

V12.1.6 边界：任务栏只承接高风险 / 高时效 / 需要人工执行的事项；低风险和观察信号不作为前端待办展示。任务生成必须先来自经营判断，再由 task_evidence_gate_service 检查关键证据。缺关键证据时降级为“经营证据补齐任务”。

## 任务详情 / 报告

```text
GET /api/modules/task-reports/tasks/{task_id}
GET /api/modules/task-reports/candidates/{module}/{id}
GET /api/modules/task-reports/alerts/{id}
```

用途：解释为什么预警、怎么处理、需要什么证据。任务进入执行队列后，详情页必须可打开。

## 数据导入

```text
GET    /api/data/templates
GET    /api/data/source-connections
POST   /api/data/source-connections/{source_id}/sync
POST   /api/data/upload/preview
POST   /api/data/upload/confirm
POST   /api/data/preview
POST   /api/data/import/confirm
POST   /api/data/import/report
POST   /api/data/import/mock-alerts
GET    /api/data/metric-facts/summary
GET    /api/data/data-gaps/summary
GET    /api/data/import-diagnostics
GET    /api/data/import-diagnostics?dataVersion={data_version}
GET    /api/data/import-records
GET    /api/data/versions
GET    /api/data/latest-version
GET    /api/data/versions/{data_version}/detail
POST   /api/data/versions/{data_version}/rollback
DELETE /api/data/versions/{data_version}?confirm=true
```

用途：Excel / CSV / JSON 上传、报表画像、字段映射、事实入库、缺口留痕、导入诊断、数据版本、测试记录清理、回滚。

边界：`/api/data/upload/*` 只负责文件解析、Sheet 识别、字段读取、经营对象同步、指标事实入库、数据缺口留痕和导入诊断；不得提前写死经营建议。任务只能由趋势/经营信号触发，并经过证据闸门。

导入结果必须携带或同步生成：

```text
经营商品主档 operating_products
经营店铺主档 operating_stores
独立事实表 product_metric_facts / store_metric_facts / traffic_source_facts
数据缺口池 data_gap_events
导入诊断 importDiagnostics
业务信号 business_signals_v6
任务证据闸门结果 evidenceGateSync
v116 闭环反查结果
```

## 趋势

```text
GET  /api/trends/summary
POST /api/trends/metric-evidence
POST /api/trends/task-sop
```

用途：指标趋势、信号证据、任务 SOP。

V12.1.6 边界：趋势信号可以完整保留，但任务进入待办前必须经过证据闸门；普通缺口不得直接生成任务。

## LLM / Agent

```text
GET  /api/llm/status
POST /api/llm/generate
GET  /api/llm/traces
GET  /api/llm/tools
GET  /api/llm/tools/{tool_name}
GET  /api/llm/mcp
```

用途：LLM 状态、Agent 生成、trace、工具网关、MCP adapter。

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

用途：健康检查、系统状态、Repository 模式、PostgreSQL cutover、经营对象回填、Demo 全运行态清理。

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

用途：当前产品基线和验收守卫。V12.1.6 MVP 验收以真实报表导入后的经营对象、指标事实、缺口池、导入诊断、证据闸门、队列和详情页稳定性为主。
