# API 重构计划

## 1. 背景

当前 FastAPI 已经实现 V7 API Demo，但主要接口仍集中在 `src/api/main.py` 中。

这适合 Demo 阶段，但不适合产品阶段。

下一步需要按照产品模块拆分 API 路由，让后端结构对应产品信息架构。

## 2. 当前 API 状态

当前已有接口：

```text
GET  /api/health
GET  /api/demo/run
GET  /api/demo/report
GET  /api/evals/run
POST /api/tasks/{task_id}/approve
POST /api/tasks/{task_id}/reject
GET  /api/tasks/status
```

当前问题：

```text
接口偏 Demo
main.py 职责过重
缺少 Data / Product / Customer / Task / Approval / Report 分层
没有独立 routes
没有持久化 repository
```

## 3. 目标 API 结构

推荐目录：

```text
src/api/
├── main.py
└── routes/
    ├── health.py
    ├── data_import.py
    ├── products.py
    ├── customers.py
    ├── diagnosis.py
    ├── tasks.py
    ├── approvals.py
    ├── reports.py
    └── evals.py
```

## 4. 推荐接口

### 4.1 Health

```text
GET /api/health
```

### 4.2 Data Import

```text
POST /api/data/import
GET  /api/data/imports
GET  /api/data/imports/{import_id}
```

### 4.3 Products

```text
GET /api/products
GET /api/products/{product_id}
GET /api/products/{product_id}/diagnosis
POST /api/products/{product_id}/diagnosis/run
```

### 4.4 Customers

```text
GET /api/customers
GET /api/customers/{customer_id}
GET /api/customers/segments
POST /api/customers/segmentation/run
```

### 4.5 Diagnosis

```text
POST /api/diagnosis/run
GET  /api/diagnosis/{diagnosis_id}
```

### 4.6 Tasks

```text
GET /api/tasks
GET /api/tasks/{task_id}
POST /api/tasks/generate
```

### 4.7 Approvals

```text
GET  /api/approvals
POST /api/approvals/{task_id}/approve
POST /api/approvals/{task_id}/reject
POST /api/approvals/{task_id}/modify
```

### 4.8 Reports

```text
GET  /api/reports
GET  /api/reports/{report_id}
POST /api/reports/generate
```

### 4.9 Evals

```text
GET /api/evals/run
```

## 5. 重构顺序

### Step 1：拆 routes

先不改业务逻辑，只把现有接口从 `main.py` 拆到 `routes/`。

### Step 2：增加 service 层

将 workflow 调用迁移到：

```text
src/services/workflow_service.py
src/services/task_service.py
src/services/approval_service.py
```

### Step 3：增加 repository 层

先用 JSON / JSONL 存储，后续替换 SQLite。

```text
src/repositories/task_repository.py
src/repositories/approval_repository.py
src/repositories/workflow_log_repository.py
```

### Step 4：前端按模块调用 API

前端从 `/api/demo/run` 逐步改为调用：

```text
/api/products
/api/customers
/api/diagnosis/run
/api/tasks
/api/approvals
/api/reports
```

## 6. 当前不做

```text
不接真实 ERP / CRM
不接真实店铺后台
不执行真实 RPA
不引入复杂权限系统
不一次性上数据库
```

## 7. 结论

API 重构的目标不是复杂化代码，而是让后端结构对齐产品模块。
