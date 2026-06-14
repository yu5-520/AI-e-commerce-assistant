# 下一轮 Sprint 计划

## Sprint 目标

将当前项目从“静态前端 + Python 命令行 Workflow”升级为“前后端可交互 Demo”。

## Sprint 1：FastAPI 后端

### 任务

- [ ] 新增 `src/api/__init__.py`
- [ ] 新增 `src/api/main.py`
- [ ] 实现 `/api/health`
- [ ] 实现 `/api/demo/run`
- [ ] 实现 `/api/evals/run`

### 验收

- [ ] 浏览器访问 `/api/health` 返回 ok
- [ ] `/api/demo/run` 返回 product_diagnosis、customer_segmentation、rpa_tasks、rag_context
- [ ] `/api/evals/run` 返回评测结果

## Sprint 2：前端连接 API

### 任务

- [ ] 修改 `web_demo/app.js`
- [ ] 将内置 Mock 数据替换为 `fetch('/api/demo/run')`
- [ ] 增加 loading 状态
- [ ] 增加 API 错误提示

### 验收

- [ ] 点击按钮后能展示真实后端返回结果
- [ ] 后端异常时页面有提示

## Sprint 3：任务审批流

### 任务

- [ ] 新增任务确认接口
- [ ] 新增任务拒绝接口
- [ ] 前端增加确认 / 拒绝按钮
- [ ] 保存审批状态

### 验收

- [ ] 任务可以从 pending_approval 变为 approved / rejected
- [ ] 日志记录用户动作

## Sprint 4：轻量日志存储

### 任务

- [ ] 增加 JSON 日志或 SQLite
- [ ] 保存 workflow_run
- [ ] 保存 approval_record
- [ ] 保存 rpa_execution_log

### 验收

- [ ] 每次 Demo 运行都有记录
- [ ] 每个任务确认 / 拒绝都有记录

## Sprint 结论

下一轮优先完成 API 化，而不是继续横向增加概念。
