# 前端从静态 Demo 过渡到 API Demo

## 1. 当前状态

当前 `web_demo/` 是静态页面，页面里的数据写在 `app.js` 中，用于快速展示三段式流程。

优势：

- 不需要启动服务。
- 可以直接打开浏览器演示。
- 适合面试中快速说明业务流程。

限制：

- 页面暂未调用 `src/run_demo.py`。
- 页面展示的是样例数据，不是实时运行结果。
- 还没有用户确认 / 拒绝 / 修改的真实交互状态回写。

## 2. API 化目标

下一阶段将前端按钮改为调用后端 API。

```text
web_demo 点击按钮
↓
API 调用 Python 工作流
↓
返回 JSON
↓
前端渲染诊断结果和任务草案
```

## 3. 推荐目录

```text
src/api/
├── __init__.py
└── main.py
```

## 4. 推荐接口

```text
GET /api/demo/run
GET /api/demo/report
GET /api/evals/run
POST /api/tasks/{task_id}/approve
POST /api/tasks/{task_id}/reject
```

## 5. 前端改造点

当前：

```javascript
const diagnosis = [...]
```

后续：

```javascript
const response = await fetch('/api/demo/run')
const data = await response.json()
```

## 6. 设计原则

即使 API 化，也不改变项目边界：

- 不自动改价
- 不自动投放
- 不自动群发客户
- 不自动处理退款
- 所有高风险任务必须人工确认

## 7. 结论

当前阶段优先满足“可展示”，下一阶段升级为“可交互”。
