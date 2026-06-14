# API 冒烟测试更新日志

## 2026-06-14：新增 API 自动化冒烟测试

### 背景

当前产品已经包含多个核心模块：

```text
Data Import
Diagnosis
Tasks
Approvals
Reports
Logs
System Status
SQLite Persistence
```

随着接口增多，继续手动验证容易漏掉问题。因此新增一个轻量 API 冒烟测试，用来检查关键接口是否还能正常返回。

## 本轮新增

### 测试脚本

```text
scripts/smoke_test_api.py
```

运行方式：

```bash
python scripts/smoke_test_api.py
```

该脚本使用 FastAPI `TestClient`，不需要先启动 uvicorn。

### CI 工作流

```text
.github/workflows/api-smoke.yml
```

触发方式：

```text
push main
pull_request main
workflow_dispatch
```

### 依赖更新

```text
requirements.txt
```

新增：

```text
httpx>=0.27.0
```

用于 FastAPI TestClient。

## 当前覆盖接口

```text
GET  /api/health
GET  /api/system/db-status
POST /api/system/clear-demo-data
POST /api/data/validate
POST /api/data/import/mock
GET  /api/data/imports
GET  /api/demo/run
POST /api/approvals/{task_id}/approve
POST /api/approvals/{task_id}/reject
GET  /api/approvals/records
GET  /api/tasks
GET  /api/reports
GET  /api/reports/demo
GET  /api/logs/workflow-runs
GET  /api/logs/execution-logs
GET  /api/logs/workflow-runs/{workflow_run_id}/execution-logs
```

## 特别检查

清空 Demo 数据接口会验证：

```text
不传 confirm=true 时必须返回 400
```

也就是说，冒烟测试会确认清空数据接口有安全保护，不会被误触发。

## 当前边界

这不是完整单元测试，也不是完整集成测试。

它只检查产品关键 API 的最小可用性：

```text
接口能启动
核心返回结构存在
关键状态能写入
日志能查询
系统状态能读取
危险操作有确认保护
```

## 下一步

继续做：

```text
按模块拆分 pytest 测试
SQLite 临时测试库隔离
前端静态资源加载检查
GitHub Actions artifact 保存测试报告
```
