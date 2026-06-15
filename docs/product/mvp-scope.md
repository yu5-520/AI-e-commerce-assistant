# MVP 范围

## 1. 当前 MVP 定义

当前 v1.0.2 MVP 是一个单页 AI ERP 经营单元工作台。

```text
ERP / CRM Mock 数据
↓
数据校验与加载
↓
经营单元识别
↓
循环频率策略
↓
商品体检、竞品机会、上新建议、流量复盘
↓
经营循环总控
↓
人工确认 / 拒绝待确认动作
↓
经营报告
↓
运行记录与审批记录
```

当前产品不是未来完整多页面 ERP，也不是旧的标题 / 图片生成 demo。

## 2. 当前必须保留

```text
src.api.main:app
/api/business/*
web_demo/index.html
web_demo/app-v2.js
scripts/check_version_governance.py
scripts/smoke_test_runtime.py
scripts/smoke_test_api.py
versioning/CHANGELOG.md
versioning/VERSION.md
docs/product/CHANGELOG.md
```

## 3. 当前产品接口

当前前端只应调用：

```text
GET  /api/business/today
GET  /api/business/operating-unit
GET  /api/business/data-health
GET  /api/business/products
GET  /api/business/competitors
GET  /api/business/listing
GET  /api/business/traffic
GET  /api/business/actions
GET  /api/business/report
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
POST /api/system/clear-demo-data?confirm=true
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
curl http://127.0.0.1:3000/api/business/today
curl http://127.0.0.1:3000/api/business/report
```

前端必须通过：

```text
web_demo/index.html
↓
web_demo/app-v2.js
↓
/api/business/*
```

## 5. 当前不做

```text
不接真实 ERP API
不接真实 CRM API
不登录真实店铺后台
不执行真实 RPA
不自动改价
不自动上架 / 下架
不自动报名活动
不自动投放广告
不自动群发客户
不自动处理退款
不保存真实客户隐私
不恢复旧 demo 入口
不恢复旧 Agent 链路
不恢复旧 evals 暴露接口
```

## 6. 已从当前主分支移除

以下内容只从 Git 历史回看，不放在 active trunk：

```text
src/run_demo.py
evals/run_evals.py
web_demo/app.js
scripts/material_observer.py
agents/
runtime/agent_registry.json
/api/demo
/api/products
/api/customers
/api/diagnosis
/api/tasks
/api/reports
/api/evals
/api/logs
```

## 7. 当前结论

当前阶段只追求：

> 用 Mock ERP / CRM 数据跑通经营单元识别、经营建议、待确认动作、经营报告和版本可追溯闭环。

任何新增页面、接口、Agent、脚本或文档，都必须先确认不会把仓库拉回旧 demo 或旧多页面蓝图。
