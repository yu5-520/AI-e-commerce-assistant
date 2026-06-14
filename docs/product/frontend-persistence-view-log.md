# 前端持久化视图更新日志

## 2026-06-14：前端展示 SQLite 业务状态

### 背景

上一轮已经将业务状态写入 SQLite：

```text
import_records
approval_records
task_status
report_records
workflow_runs
execution_logs
```

但前端仍主要展示当前工作流返回的数据，没有充分体现持久化状态。

本轮把这些持久化对象真正展示到工作台页面。

## 本轮更新

### 任务中心

现在任务中心会调用：

```text
GET /api/tasks
```

该接口会合并当前任务草案与 SQLite 中的 task_status。

页面展示：

```text
task_id
task_type
risk_level
approval_status / status
auto_execution_allowed
```

### 审批中心

现在审批中心会调用：

```text
GET /api/approvals/records
```

页面除了展示待确认任务，也展示 ApprovalRecord 历史。

### 报告中心

现在报告中心会调用：

```text
GET /api/reports
GET /api/reports/demo
```

页面展示 ReportRecord 列表和 Markdown 报告内容。

### 运行日志

现在运行日志页支持：

```text
查看 WorkflowRun 列表
查看最新 ExecutionLog
点击某个 workflow_run_id 查看该运行的节点日志
```

调用接口：

```text
GET /api/logs/workflow-runs
GET /api/logs/execution-logs
GET /api/logs/workflow-runs/{workflow_run_id}/execution-logs
```

## 更新文件

```text
web_demo/app.js
web_demo/data-import.css
web_demo/README.md
```

## 当前价值

前端从“只展示当前一次工作流结果”，升级为“展示可持久化的产品状态”。

这一步后，产品具备了更完整的闭环：

```text
运行动作
↓
写入 SQLite
↓
前端读取状态
↓
用户查看历史与当前状态
```

## 下一步

继续做：

```text
SQLite 初始化/健康检查 API
数据库表状态页
日志分页与筛选
按 workflow_type / status 查询
```
