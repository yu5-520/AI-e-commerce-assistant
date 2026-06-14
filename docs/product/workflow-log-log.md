# WorkflowRun / ExecutionLog 更新日志

## 2026-06-14：新增产品级运行日志

### 背景

此前系统已经有导入记录和审批记录，但还没有统一的产品级运行日志。

产品阶段需要记录每一次关键动作：

```text
数据导入
诊断运行
RAG 召回
任务生成
审批确认 / 拒绝
报告输出
```

因此新增 WorkflowRun 和 ExecutionLog。

## 本轮新增

### 服务层

```text
src/services/log_service.py
```

负责：

```text
create_workflow_run
finish_workflow_run
create_execution_log
list_workflow_runs
list_execution_logs
list_execution_logs_by_run
```

### API 层

```text
src/api/routes/logs.py
```

新增接口：

```text
GET /api/logs/workflow-runs
GET /api/logs/execution-logs
GET /api/logs/workflow-runs/{workflow_run_id}/execution-logs
```

### 前端层

新增侧边栏模块：

```text
运行日志
```

展示：

```text
WorkflowRun
ExecutionLog
```

## 当前已接入日志的动作

```text
/api/demo/run
/api/diagnosis/run
/api/data/import/mock
/api/approvals/{task_id}/approve
/api/approvals/{task_id}/reject
```

## 当前日志文件

```text
logs/workflow_runs.jsonl
logs/execution_logs.jsonl
logs/data_import_records.jsonl
logs/approval_records.jsonl
```

## 当前边界

当前仍然使用 JSONL 轻量存储，不引入数据库。

后续可替换为：

```text
SQLite
PostgreSQL
workflow_runs 表
execution_logs 表
approval_records 表
import_records 表
```

## 下一步

继续做产品持久化：

```text
SQLite repository 层
Task 状态持久化
Approval 状态持久化
WorkflowRun 查询详情页
```
