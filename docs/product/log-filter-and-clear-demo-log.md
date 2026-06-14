# 日志筛选与清空 Demo 数据更新日志

## 2026-06-14：新增日志分页、筛选与清空 Demo 数据能力

### 背景

系统已经具备 WorkflowRun、ExecutionLog、SQLite 持久化和系统状态页。

但日志列表越来越长后，需要基本的筛选和分页；同时演示过程中也需要一个安全方式清空运行时数据，方便重新演示产品闭环。

## 本轮新增

### 日志 API 分页与筛选

更新：

```text
src/api/routes/logs.py
```

新增 query 参数：

```text
limit
offset
workflow_type
status
```

接口返回结构从纯数组升级为：

```text
items
total
limit
offset
filters
```

支持接口：

```text
GET /api/logs/workflow-runs
GET /api/logs/execution-logs
GET /api/logs/workflow-runs/{workflow_run_id}/execution-logs
```

### 清空 Demo 数据 API

更新：

```text
src/services/system_service.py
src/api/routes/system.py
```

新增接口：

```text
POST /api/system/clear-demo-data?confirm=true&include_audit_logs=true
```

安全策略：

```text
必须显式传 confirm=true
只删除 logs/ 下运行生成的数据
不删除源码
不删除 Mock 数据
不删除 docs/product 产品文档
清空后自动重建空 SQLite 表结构
```

### 前端稳定入口

新增：

```text
web_demo/app-v2.js
```

并更新：

```text
web_demo/index.html
```

现在页面加载 `app-v2.js` 作为稳定入口。

### 前端新增能力

运行日志页新增：

```text
按 workflow_type 筛选
按 status 筛选
选择显示条数
重置筛选
点击 WorkflowRun 查看节点日志
```

系统状态页新增：

```text
清空 Demo 数据按钮
```

该按钮会调用：

```text
POST /api/system/clear-demo-data?confirm=true&include_audit_logs=true
```

并在前端二次确认。

## 当前价值

产品现在不只是能记录日志，还能管理演示期运行数据：

```text
运行数据可查询
运行日志可筛选
节点详情可追踪
Demo 数据可安全清空
系统状态可重新检查
```

## 下一步

继续做：

```text
按 workflow_type / status 的后端 SQL 查询优化
日志分页按钮：上一页 / 下一页
数据库备份 / 导出 Demo 数据
API 自动化冒烟测试
```
