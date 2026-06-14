# 下一阶段：前端连接后端 API 计划

## 1. 当前状态

当前项目已经具备两套 Demo：

1. Python Mock Workflow：`python -m src.run_demo`
2. 静态前端 Demo：`web_demo/index.html`

前端 Demo 目前使用内置 Mock 数据展示流程，没有直接调用 Python 工作流。

## 2. 下一阶段目标

将静态页面升级为 API 驱动页面：

```text
前端点击按钮
↓
调用后端 API
↓
后端运行 Mock Workflow
↓
返回商品诊断 / 客户分层 / RPA 任务草案 / RAG 召回结果
↓
前端渲染结果
```

## 3. 推荐 API 设计

### 3.1 GET /api/demo/run

运行完整 Mock Workflow。

返回：

```json
{
  "product_diagnosis": [],
  "customer_segmentation": [],
  "rpa_tasks": [],
  "rag_context": {},
  "approval_required_tasks": []
}
```

### 3.2 GET /api/demo/report

返回 Markdown 报告内容。

### 3.3 GET /api/evals/run

运行最小 Evals。

返回：

```json
{
  "passed": true,
  "results": []
}
```

## 4. 后端选择

MVP 阶段建议使用 FastAPI：

```text
src/api/main.py
```

原因：

- 轻量
- 易接 Python 工作流
- 适合演示 JSON API
- 后续方便接模型 API、RAG 检索和 MCP 工具

## 5. 前端升级

当前静态页面按钮可以从内置 Mock 数据改为调用：

```javascript
fetch('/api/demo/run')
```

然后将返回结果渲染到：

- ERP / CRM 摘要区
- AI / RAG 诊断区
- RPA 任务草案区
- 人工确认区

## 6. 安全边界

即使接入 API，也保持以下边界：

- 不连接真实店铺后台
- 不自动改价
- 不自动报名活动
- 不自动群发客户
- 不自动处理退款
- 不保存真实客户隐私

## 7. 设计结论

下一阶段重点不是增加更多概念，而是让前端真正消费后端工作流结果。

> 当前是“静态可演示”，下一步升级成“API 可交互”。
