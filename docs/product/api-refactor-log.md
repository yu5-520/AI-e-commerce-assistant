# API 重构日志

## 2026-06-14：从 Demo API 拆分为产品模块 API

### 背景

此前 `src/api/main.py` 集中了健康检查、Demo Workflow、Evals、任务审批等接口，适合 Demo 阶段，但不利于后续产品模块扩展。

### 本轮调整

新增 service 层：

```text
src/services/workflow_service.py
src/services/approval_service.py
src/services/eval_service.py
```

新增 route 层：

```text
src/api/routes/health.py
src/api/routes/demo.py
src/api/routes/products.py
src/api/routes/customers.py
src/api/routes/diagnosis.py
src/api/routes/tasks.py
src/api/routes/approvals.py
src/api/routes/reports.py
src/api/routes/evals.py
```

`src/api/main.py` 改为只负责：

```text
创建 FastAPI app
挂载静态前端
配置 CORS
include_router
```

### 当前接口结构

```text
GET  /api/health
GET  /api/demo/run
GET  /api/demo/report
GET  /api/products
GET  /api/products/{product_id}
GET  /api/products/{product_id}/diagnosis
GET  /api/customers
GET  /api/customers/segments
GET  /api/customers/{customer_id}
POST /api/diagnosis/run
GET  /api/tasks
GET  /api/tasks/approval-required
GET  /api/tasks/status
GET  /api/tasks/{task_id}
GET  /api/approvals
POST /api/approvals/{task_id}/approve
POST /api/approvals/{task_id}/reject
GET  /api/reports
GET  /api/reports/demo
GET  /api/evals/run
```

### 兼容性

保留 `/api/demo/run`，保证当前前端不需要立即重写。

同时新增产品模块接口，为后续前端从单页 Demo 过渡到产品工作台提供接口基础。

### 当前仍不做

```text
不接真实 ERP / CRM
不执行真实 RPA
不自动改价
不自动群发客户
不引入复杂权限系统
```

## 下一步

继续重构前端：从单页 Demo 改为带侧边栏的多模块工作台。
