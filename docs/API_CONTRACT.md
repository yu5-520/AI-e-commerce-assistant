# API_CONTRACT

本文件只记录当前前端和当前主架构会使用的 API。历史接口不进入本文件。

## 账号

```text
/api/accounts
/api/accounts/me
/api/accounts/switch
/api/accounts/users
/api/accounts/users/{user_id}/role
/api/accounts/users/{user_id}/stores
/api/accounts/store-assignments
/api/accounts/store-assignments/{store_id}
/api/accounts/roles
/api/accounts/roles/{role_id}/permissions
```

用途：账号切换、角色权限、店铺归属、老板 / 总管 / 运营视图。

## 模块

```text
/api/modules/dashboard
/api/modules/operating-unit
/api/modules/product
/api/modules/competitor
/api/modules/listing
/api/modules/traffic
/api/modules/report
/api/modules/log
```

用途：总览、经营、报表、日志页面数据。

## 任务

```text
/api/modules/todo
/api/modules/todo/events
/api/modules/todo/counters
/api/modules/todo/{task_id}/evidence
/api/modules/todo/{task_id}/split
/api/modules/todo/{task_id}/assign
/api/modules/todo/{task_id}/accept
/api/modules/todo/{task_id}/submit
/api/modules/todo/{task_id}/submit-evidence
/api/modules/todo/{task_id}/review
/api/modules/todo/{task_id}/review-evidence
/api/modules/todo/{task_id}/recap
/api/modules/todo/{task_id}/complete
/api/modules/todo/reset
```

用途：统一任务池、跨账号流转、证据提交、总管复核、任务完成。

## 任务详情 / 报告

```text
/api/modules/task-reports/tasks/{task_id}
/api/modules/task-reports/candidates/{module}/{id}
/api/modules/task-reports/alerts/{id}
```

用途：解释为什么预警、怎么处理、需要什么证据。

## 数据导入

```text
/api/data/templates
/api/data/source-connections
/api/data/source-connections/{source_id}/sync
/api/data/preview
/api/data/import/confirm
/api/data/import/report
/api/data/import/mock-alerts
/api/data/import-records
/api/data/versions
/api/data/latest-version
/api/data/versions/{data_version}
/api/data/versions/{data_version}/rollback
```

用途：报表模板、字段映射、报表导入、数据版本、测试记录清理、回滚。

## 趋势

```text
/api/trends/summary
/api/trends/metric-evidence
/api/trends/task-sop
```

用途：指标趋势、信号证据、任务 SOP。

## LLM / Agent

```text
/api/llm/status
/api/llm/generate
/api/llm/traces
/api/llm/tools
/api/llm/tools/{tool_name}
/api/llm/mcp
```

用途：LLM 状态、Agent 生成、trace、工具网关、MCP adapter。

## 系统

```text
/api/health
/api/system/db-status
/api/system/security
/api/system/repositories
/api/system/repositories?check=true
/api/system/postgres-cutover-check
/api/system/reset-runtime-data?confirm=true
/api/system/clear-runtime-data?confirm=true
```

用途：健康检查、系统状态、Repository 模式、PostgreSQL cutover、Demo 清理。

## 架构验收

```text
/api/architecture/v10/task-driven-product
/api/architecture/v10/readiness
```

用途：当前 V10 任务驱动产品基线和验收守卫。
