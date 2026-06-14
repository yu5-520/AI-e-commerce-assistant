# 下一优先级：API 化

## 1. 为什么 API 化是下一步

当前项目已经有：

- Python Mock Workflow
- 静态前端 Demo
- Evals
- 文档和样例输出

但前端还没有调用真实 Python Workflow。

因此下一步最重要的是 API 化。

## 2. API 化后项目会发生什么变化

当前：

```text
前端展示内置样例数据
Python 单独运行工作流
```

升级后：

```text
前端点击按钮
↓
调用后端 API
↓
后端运行 Python Workflow
↓
返回真实 JSON
↓
前端渲染结果
```

## 3. 需要新增

```text
src/api/__init__.py
src/api/main.py
requirements.txt
```

## 4. 推荐接口

```text
GET /api/health
GET /api/demo/run
GET /api/evals/run
POST /api/tasks/{task_id}/approve
POST /api/tasks/{task_id}/reject
```

## 5. 完成后的简历表达

> 基于 FastAPI 封装 AI 工作流接口，将 Mock ERP / CRM 数据诊断、RAG 召回、RPA 任务草案和 Evals 评测开放为前端可调用 API，实现前后端可交互 Demo。
