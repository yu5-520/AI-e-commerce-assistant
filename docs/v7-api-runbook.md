# V7 API Runbook

## 1. 目标

V7 将 V6 的 Python Mock Workflow 封装成 FastAPI API，并让前端优先调用后端结果。

当前仍然只使用 Mock ERP / CRM 数据，不连接真实店铺后台，不执行真实 RPA 操作。

## 2. 安装依赖

```bash
pip install -r requirements.txt
```

## 3. 启动 API

```bash
uvicorn src.api.main:app --reload
```

启动后访问：

```text
http://127.0.0.1:8000/
```

或 API 文档：

```text
http://127.0.0.1:8000/docs
```

## 4. API 列表

```text
GET  /api/health
GET  /api/demo/run
GET  /api/demo/report
GET  /api/evals/run
POST /api/tasks/{task_id}/approve
POST /api/tasks/{task_id}/reject
GET  /api/tasks/status
```

## 5. 前端联动

前端文件：

```text
web_demo/index.html
web_demo/app.js
web_demo/styles.css
```

启动 API 后打开：

```text
http://127.0.0.1:8000/web_demo/index.html
```

页面会调用：

```text
/api/demo/run
```

如果 API 不可用，页面自动回退到本地样例模式。

## 6. 任务审批流

任务卡片包含确认和拒绝按钮。

确认调用：

```text
POST /api/tasks/{task_id}/approve
```

拒绝调用：

```text
POST /api/tasks/{task_id}/reject
```

当前 V7 只记录审批状态，不执行真实 RPA 动作。

审批日志写入：

```text
logs/approval_records.jsonl
```

## 7. 安全边界

V7 仍然不做：

- 真实 ERP / CRM 接入
- 真实店铺后台接入
- 自动改价
- 自动投放
- 自动报名活动
- 自动群发客户
- 自动处理退款

## 8. 结论

V7 的价值是把项目从“命令行可运行 + 静态前端可展示”升级为“前后端可交互 Demo”。
