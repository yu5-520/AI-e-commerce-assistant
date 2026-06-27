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
GET /api/modules/competitor
GET /api/modules/listing
GET /api/modules/traffic
GET /api/modules/report
GET /api/modules/log
```

用途：总览、经营、商品、竞品、上新、流量、数据、日志页面数据。

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

V11 边界：任务栏只承接高风险 / 高时效 / 需要人工执行的事项；低风险和观察信号不作为前端待办展示。

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
GET    /api/data/import-records
GET    /api/data/versions
GET    /api/data/latest-version
GET    /api/data/versions/{data_version}/detail
POST   /api/data/versions/{data_version}/rollback
DELETE /api/data/versions/{data_version}?confirm=true
```

用途：Excel / CSV / JSON 上传、报表模板、字段映射、报表导入、数据版本、测试记录清理、回滚。

边界：`/api/data/upload/*` 只负责文件解析、Sheet 识别、字段读取和标准化入库，不提前写风险判断、任务线索或经营建议。

导入结果必须携带或同步生成：

```text
商品入库ID识别
经营商品主档 operating_products
经营店铺主档 operating_stores
商品标签
店铺聚合
店铺权重
店铺标签
业务信号 business_signals_v6
高风险执行任务
中低风险标签 / 观察信号
v116 闭环反查结果
```

## 趋势

```text
GET  /api/trends/summary
POST /api/trends/metric-evidence
POST /api/trends/task-sop
```

用途：指标趋势、信号证据、任务 SOP。

V11 边界：趋势信号可以完整保留，但低风险趋势只进入后端标签和观察，不进入前端任务栏。

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
```

## 架构验收

```text
GET /api/architecture/v10/task-driven-product
GET /api/architecture/v10/readiness
```

用途：当前产品基线和验收守卫。V11 MVP 测验阶段以真实报表导入后的经营对象、标签、队列和详情页稳定性为主验收。
