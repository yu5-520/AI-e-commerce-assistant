# Web Demo

这是 AI + RPA + ERP + CRM 电商经营自动化工作台的前端 Demo。

V7 起，页面支持两种模式：

1. **API 模式**：启动 FastAPI 后，页面调用 `/api/demo/run` 获取真实 Python Mock Workflow 输出。
2. **本地样例模式**：未启动 API 时，页面自动回退到内置样例数据，方便直接打开展示。

## 运行方式一：API 模式

在仓库根目录安装依赖：

```bash
pip install -r requirements.txt
```

启动服务：

```bash
uvicorn src.api.main:app --reload
```

然后打开：

```text
http://127.0.0.1:8000/
```

或：

```text
http://127.0.0.1:8000/web_demo/index.html
```

## 运行方式二：本地样例模式

直接用浏览器打开：

```text
web_demo/index.html
```

这种方式不会调用 API，只展示内置样例数据。

## 页面流程

```text
导入 Mock 数据
↓
生成 AI / RAG 诊断
↓
生成 RPA 任务草案
↓
查看人工确认项
```

## API 能力

当前前端会优先调用：

```text
GET /api/demo/run
POST /api/tasks/{task_id}/approve
POST /api/tasks/{task_id}/reject
```

如果 API 不可用，自动回退到本地样例模式。

## 当前边界

当前页面和 API 都不连接真实 ERP / CRM，不执行真实店铺后台操作，不自动改价、不自动投放、不自动群发、不自动退款。
