# Release Notes V7

## 版本名称

V7：API 可交互 Demo

## 版本目标

将 V6 的“静态前端 Demo + Python Mock Workflow”升级为“FastAPI 后端 + 前端 fetch API”的可交互 Demo。

## 新增能力

- 新增 FastAPI 后端。
- 新增 `/api/health` 健康检查。
- 新增 `/api/demo/run`，返回完整 Mock Workflow 输出。
- 新增 `/api/demo/report`，返回 Markdown 报告。
- 新增 `/api/evals/run`，运行最小 Evals。
- 新增任务确认接口 `/api/tasks/{task_id}/approve`。
- 新增任务拒绝接口 `/api/tasks/{task_id}/reject`。
- 前端优先调用 API，API 不可用时回退本地样例数据。
- CLI 和 API 复用同一个 `src.workflow.mock_workflow` 编排服务。

## 新增文件

```text
requirements.txt
src/workflow/__init__.py
src/workflow/mock_workflow.py
src/api/__init__.py
src/api/main.py
docs/v7-api-runbook.md
docs/release-notes-v7.md
```

## 更新文件

```text
README.md
src/run_demo.py
web_demo/app.js
web_demo/styles.css
web_demo/README.md
```

## 当前边界

V7 仍然不接真实 ERP / CRM，不接真实店铺后台，不自动执行 RPA 高风险动作。

任务确认 / 拒绝只记录状态，不触发真实操作。

## 下一步

V8 可以考虑：

```text
SQLite 日志存储
↓
任务状态持久化
↓
LLM 节点替换规则诊断
↓
Embedding + 向量库替换关键词 RAG
```
