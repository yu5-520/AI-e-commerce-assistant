# 系统状态页更新日志

## 2026-06-14：新增数据库健康检查与系统状态页

### 背景

当前产品已经具备 SQLite 持久化能力，保存以下对象：

```text
WorkflowRun
ExecutionLog
ImportRecord
ApprovalRecord
TaskStatus
ReportRecord
```

但前端还缺少一个统一入口，用于检查数据库是否生成、表是否存在、记录数是否正常。

## 本轮新增

### 服务层

```text
src/services/system_service.py
```

负责读取 SQLite 状态：

```text
数据库文件是否存在
数据库文件路径
数据库文件大小
表数量
每张表的记录数
每张表的最近更新时间
系统运行边界
```

### API 层

```text
src/api/routes/system.py
```

新增接口：

```text
GET /api/system/db-status
```

### 前端层

更新：

```text
web_demo/index.html
web_demo/app.js
web_demo/README.md
```

新增侧边栏模块：

```text
系统状态
```

页面展示：

```text
数据库是否生成
SQLite 文件路径
表数量
总记录数
文件大小
每张表记录数
每张表最近更新时间
```

## 当前检查表

```text
workflow_runs
execution_logs
import_records
approval_records
task_status
report_records
```

## 当前价值

这一步让产品从“有持久化”升级到“能检查持久化是否正常”。

对后续部署、调试、演示都很关键，因为用户可以直接看到：

```text
系统有没有生成数据库
哪些表已经有数据
哪些表还没有数据
最近一次写入发生在什么时候
```

## 下一步

继续做：

```text
日志分页
按 workflow_type 查询
按 status 查询
数据库重建 / 清空 Demo 数据按钮
```
