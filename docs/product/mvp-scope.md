# MVP 范围

## 1. 当前 MVP 定义

当前 v2.0.0 MVP 是一个 AI ERP 经营单元协同工作台。

```text
ERP / CRM Mock 数据
↓
数据校验与加载
↓
经营单元识别
↓
商品、竞品、上新、流量、报表模块
↓
候选预警与详情报告
↓
统一任务池
↓
账号角色 / 权限 / 店群范围
↓
任务派发 / 运营提交 / 总管复核
↓
日志记录与复盘
```

当前产品不是完整 ERP、完整 CRM、真实登录系统，也不是自动运营 Agent。

## 2. 当前必须保留

```text
src.api.main:app
/api/modules/*
/api/accounts
web_demo/index.html
web_demo/core/router.js
web_demo/core/api-client.js
web_demo/stores/task-store.js
web_demo/modules/*/page.js
scripts/check_version_governance.py
scripts/smoke_test_runtime.py
scripts/smoke_test_api.py
versioning/CHANGELOG.md
versioning/VERSION.md
docs/product/CHANGELOG.md
```

## 3. 当前产品接口

模块接口：

```text
GET  /api/modules/dashboard
GET  /api/modules/operating-unit
GET  /api/modules/product
GET  /api/modules/competitor
GET  /api/modules/listing
GET  /api/modules/traffic
GET  /api/modules/report
GET  /api/modules/todo
GET  /api/modules/log
GET  /api/modules/task-reports/tasks/{task_id}
GET  /api/modules/task-reports/candidates/{module}/{entity_id}
```

账号与任务协同接口：

```text
GET  /api/accounts
GET  /api/accounts/me
GET  /api/accounts/users
GET  /api/accounts/roles
GET  /api/accounts/permissions
GET  /api/accounts/store-groups
GET  /api/accounts/stores
POST /api/modules/todo/{task_id}/assign
POST /api/modules/todo/{task_id}/submit
POST /api/modules/todo/{task_id}/review
POST /api/modules/todo/{task_id}/complete
POST /api/modules/todo/{task_id}/pin
POST /api/modules/todo/{task_id}/reorder
POST /api/modules/todo/reset
```

辅助接口：

```text
GET  /api/health
POST /api/data/validate
POST /api/data/import/mock
GET  /api/data/imports
GET  /api/approvals
GET  /api/approvals/records
POST /api/approvals/{task_id}/approve
POST /api/approvals/{task_id}/reject
GET  /api/system/db-status
POST /api/system/clear-runtime-data?confirm=true
```

## 4. 当前验收标准

本地脚本必须通过：

```bash
python scripts/check_version_governance.py
python scripts/smoke_test_runtime.py
python scripts/smoke_test_api.py
```

服务必须可以启动：

```bash
uvicorn src.api.main:app --host 127.0.0.1 --port 3000
```

关键接口必须可访问：

```bash
curl http://127.0.0.1:3000/api/health
curl http://127.0.0.1:3000/api/modules/dashboard
curl http://127.0.0.1:3000/api/accounts
```

前端必须通过：

```text
web_demo/index.html
↓
web_demo/core/router.js
↓
web_demo/modules/*/page.js
↓
/api/modules/* + /api/accounts
```

## 5. 当前不做

```text
不接真实 ERP API
不接真实 CRM API
不登录真实店铺后台
不接真实企业 SSO
不执行真实 RPA
不自动改价
不自动上架 / 下架
不自动报名活动
不自动投放广告
不自动群发客户
不自动处理退款
不保存真实客户隐私
```

## 6. 账号系统边界

```text
老板账号：全局观察、下发任务、查看复核结果。
店群总管账号：拆分任务、派发运营、复核提交。
运营账号：只处理自己的任务并提交。
数据 / 财务账号：看报表和财务数据，不直接处理运营任务。
只读观察账号：只读看板、报告、日志。
```

## 7. 当前结论

当前阶段只追求：

> 用 Mock ERP / CRM 数据跑通经营单元识别、候选预警、详情报告、统一任务池、账号协同、派发提交复核和日志归档闭环。

任何新增页面、接口、Agent、脚本或文档，都必须先确认不会偏离当前可运行主线。
