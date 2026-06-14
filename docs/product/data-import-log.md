# Data Import 更新日志

## 2026-06-14：Mock CSV 数据导入产品化

### 背景

此前“数据导入”只是前端页面里的展示区域，实际仍然依赖 `/api/demo/run` 一次性跑完整工作流。

产品阶段需要把“数据进入系统”单独拆出来，形成 Data Hub 的最小能力：数据源、字段校验、关系校验、导入记录。

### 本轮新增

新增服务层：

```text
src/services/data_import_service.py
```

新增 API 路由：

```text
src/api/routes/data_import.py
```

注册到：

```text
src/api/main.py
```

新增前端样式：

```text
web_demo/data-import.css
```

更新前端：

```text
web_demo/app.js
web_demo/index.html
web_demo/README.md
```

### 新增 API

```text
GET  /api/data/sources
POST /api/data/validate
POST /api/data/import/mock
GET  /api/data/imports
```

### 当前校验内容

字段校验：

```text
必填字段是否存在
必填单元格是否为空
数字字段是否为数字
```

关系校验：

```text
orders.product_id 是否存在于 products
inventory.product_id 是否存在于 products
refunds.product_id 是否存在于 products
refunds.order_id 是否存在于 orders
customer_tags.customer_id 是否存在于 customers
interactions.customer_id 是否存在于 customers
```

### 当前日志

导入记录写入：

```text
logs/data_import_records.jsonl
```

### 当前边界

当前仍然只使用 Mock CSV，不做真实文件上传，不接真实 ERP / CRM，不保存真实客户隐私。

## 下一步

继续做：

```text
上传 CSV / Excel
字段映射确认
错误行报告
WorkflowRun 日志
SQLite 持久化
```
