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

用途：执行队列、证据提交、总管复核、任务完成。

V11 边界：任务栏只承接高风险 / 高时效 / 需要人工执行的事项；低风险和观察信号不作为前端待办展示。

## 任务详情 / 报告

```text
/api/modules/task-reports/tasks/{task_id}
/api/modules/task-reports/candidates/{module}/{id}
/api/modules/task-reports/alerts/{id}
```

用途：解释为什么预警、怎么处理、需要什么证据。

V11 兜底：`/api/modules/task-reports/tasks/{task_id}` 不应因深度报告缺失直接失败。任务存在或任务ID被前端打开时，服务返回基础兜底报告，避免前端显示“报告加载失败”。

## 数据导入

```text
/api/data/templates
/api/data/source-connections
/api/data/source-connections/{source_id}/sync
/api/data/upload/preview
/api/data/upload/confirm
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

用途：Excel / CSV / JSON 上传、报表模板、字段映射、报表导入、数据版本、测试记录清理、回滚。

边界：`/api/data/upload/*` 只负责文件解析、Sheet 识别、字段读取和标准化入库，不提前写风险判断、任务线索或经营建议。

V11 导入结果必须携带或同步生成：

```text
商品入库ID识别
商品历史深度
商品标签
店铺聚合
店铺权重
店铺标签
高风险执行任务
中低风险标签/观察信号
```

## 趋势

```text
/api/trends/summary
/api/trends/metric-evidence
/api/trends/task-sop
```

用途：指标趋势、信号证据、任务 SOP。

V11 边界：趋势信号可以完整保留，但低风险趋势只进入后端标签和观察，不进入前端任务栏。

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

用途：当前产品基线和验收守卫。V11 MVP 测验阶段以真实报表导入后的标签、队列和详情页稳定性为主验收。