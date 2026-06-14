# V7 Status

V7 已开始实现，并已完成第一版 API 可交互 Demo。

当前已完成：

- FastAPI 后端入口：`src/api/main.py`
- 统一工作流服务：`src/workflow/mock_workflow.py`
- API 接口：`/api/health`、`/api/demo/run`、`/api/demo/report`、`/api/evals/run`
- 任务确认 / 拒绝接口：`/api/tasks/{task_id}/approve`、`/api/tasks/{task_id}/reject`
- 前端 `web_demo/app.js` 已支持优先调用 API，失败时回退本地样例数据

当前仍然不要写成生产级系统。

安全表述：

> 已完成 FastAPI API 原型，将 Python Mock Workflow 封装为前端可调用接口，并支持任务确认 / 拒绝状态记录；当前仍使用 Mock ERP / CRM 数据，不接真实店铺后台，不执行真实 RPA 高风险动作。
