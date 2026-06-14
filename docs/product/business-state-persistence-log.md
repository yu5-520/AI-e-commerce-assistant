# 业务状态持久化更新日志

## 2026-06-14：ImportRecord / ApprovalRecord / TaskStatus / ReportRecord 进入 SQLite

### 背景

上一轮已经将 WorkflowRun 和 ExecutionLog 双写到 JSONL + SQLite。

这一轮继续推进业务状态持久化，让产品不再依赖纯内存或单独 JSONL 文件。

## 本轮新增 SQLite 表

```text
import_records
approval_records
task_status
report_records
```

## 当前表职责

### import_records

记录一次数据导入结果。

字段：

```text
import_id
workflow_run_id
mode
status
dataset_count
total_rows
validation
created_at
```

### approval_records

记录一次用户审批动作。

字段：

```text
approval_id
workflow_run_id
task_id
approval_status
operator
risk_level
task_type
payload
created_at
```

### task_status

记录任务当前状态。

字段：

```text
task_id
workflow_run_id
task_type
risk_level
approval_status
status
auto_execution_allowed
payload
updated_at
```

### report_records

记录报告生成结果。

字段：

```text
report_id
workflow_run_id
report_type
path
format
payload
created_at
```

## 当前双写策略

仍然保留：

```text
logs/data_import_records.jsonl
logs/approval_records.jsonl
logs/workflow_runs.jsonl
logs/execution_logs.jsonl
```

同时写入：

```text
logs/product_workbench.sqlite3
```

## 当前已接入

```text
Data Import -> import_records
Approval -> approval_records + task_status
Report Output -> report_records
WorkflowRun / ExecutionLog -> workflow_runs + execution_logs
```

## 当前 API 行为

- `/api/data/imports` 优先读取 SQLite，SQLite 为空时回退 JSONL。
- `/api/approvals` 返回 SQLite 中的任务状态，并合并当前内存状态。
- `/api/approvals/records` 返回审批记录。
- `/api/reports` 优先读取 SQLite 中的报告记录。

## 下一步

继续做：

```text
Task Center 直接读取 task_status
前端显示 ApprovalRecord 历史
Report Center 显示 ReportRecord 列表
SQLite 数据库初始化/检查 API
```
