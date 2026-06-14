# SQLite 持久化更新日志

## 2026-06-14：新增 SQLite repository 层

### 背景

此前 WorkflowRun 和 ExecutionLog 已经通过 JSONL 文件记录：

```text
logs/workflow_runs.jsonl
logs/execution_logs.jsonl
```

JSONL 适合审计和查看，但不适合后续产品查询、筛选、分页、状态聚合。

因此新增 SQLite repository 层，作为轻量数据库持久化方案。

## 本轮新增

### Repository 层

```text
src/repositories/__init__.py
src/repositories/sqlite_repository.py
```

### SQLite 文件

运行后自动生成：

```text
logs/product_workbench.sqlite3
```

## 当前数据表

### workflow_runs

字段：

```text
workflow_run_id
workflow_type
status
input_snapshot
output_snapshot
started_at
finished_at
error_message
```

### execution_logs

字段：

```text
log_id
workflow_run_id
node_name
status
input_snapshot
output_snapshot
error_message
created_at
```

## 当前写入方式

当前采用“双写”：

```text
JSONL 审计日志
+
SQLite 查询存储
```

这样既保留可读日志，也为后续产品查询打基础。

## 当前已接入

```text
create_workflow_run
finish_workflow_run
create_execution_log
list_workflow_runs
list_execution_logs
list_execution_logs_by_run
```

## 当前 API 不变

前端和 API 仍然调用：

```text
GET /api/logs/workflow-runs
GET /api/logs/execution-logs
GET /api/logs/workflow-runs/{workflow_run_id}/execution-logs
```

但底层已经优先读取 SQLite，SQLite 为空时回退 JSONL。

## 下一步

继续把以下对象迁移到 SQLite：

```text
ImportRecord
ApprovalRecord
TaskStatus
ReportRecord
```

然后再考虑：

```text
分页
筛选
按 workflow_type 查询
按 status 查询
前端日志详情页
```
