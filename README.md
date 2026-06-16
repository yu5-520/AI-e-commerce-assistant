# AI ERP 经营单元电商协同系统 MVP

> 一个基于商家 ERP / CRM Mock 数据识别经营单元，并把商品、竞品、上新、流量、报表预警转成可派发任务的 AI 经营协同原型。V2.0 的重点不是自动替商家执行，而是把“老板看报告、总管派发、运营处理、总管复核、日志归档”的协同链路跑通。

## 1. 当前主定位

本仓库当前只保留一条主产品链路：

```text
ERP / CRM Mock 数据
↓
经营单元识别
↓
循环频率策略
↓
商品、竞品、上新、流量、报表模块
↓
候选预警 / 详情报告
↓
统一任务池
↓
账号角色 / 权限 / 店群范围
↓
任务派发 / 运营提交 / 总管复核
↓
日志归档
↓
/api/modules/* + /api/accounts
↓
web_demo 模块化前端
```

核心原则：

```text
ERP 决定经营单元，经营单元决定类目知识，模块生成候选预警，报告解释判断依据，账号系统决定谁能看、谁能派、谁能处理、谁能复核。
```

系统不保留旧版 demo 入口、旧版前端模板、旧 Agent 链路和旧兼容 API。历史版本由 Git commits 保存，不放在 main 分支干扰当前产品。

## 2. 当前目录职责

```text
src/api/main.py                         FastAPI 唯一入口
src/api/routes/accounts.py              V2 账号 / 角色 / 权限 API
src/api/routes/modules/__init__.py       当前模块 API 聚合入口
src/api/routes/modules/dashboard.py      总览模块
src/api/routes/modules/operating_unit.py 经营单元模块
src/api/routes/modules/product.py        商品模块
src/api/routes/modules/competitor.py     竞品模块
src/api/routes/modules/listing.py        上新模块
src/api/routes/modules/traffic.py        流量模块
src/api/routes/modules/report.py         报表模块
src/api/routes/modules/task_report.py    详情报告模块
src/api/routes/modules/todo.py           待办 / 派发 / 提交 / 复核模块
src/api/routes/modules/log.py            日志模块
src/api/routes/data_import.py            Mock 数据校验与导入记录
src/api/routes/health.py                 健康检查
src/api/routes/system.py                 系统状态与运行数据清理
src/services/account_service.py          V2 Mock 账号、角色、权限、店群范围
src/services/module_task_service.py      统一任务池与协同任务生命周期
src/services/task_report_service.py      详情报告与未来 Agent 评估边界
src/services/module_data_service.py      后端模块 Mock 数据源
src/repositories/                       SQLite / JSONL 记录层
web_demo/index.html                      当前前端入口
web_demo/core/router.js                  前端路由生命周期
web_demo/core/api-client.js              前端 API 客户端
web_demo/stores/task-store.js            前端任务状态缓存
web_demo/modules/*/page.js               模块化页面
scripts/start_server.sh                  本机启动脚本
scripts/deploy_server.sh                 服务器部署脚本
scripts/check_version_governance.py      版本治理检查脚本
scripts/smoke_test_runtime.py            当前 workflow smoke test
scripts/smoke_test_api.py                当前产品 API smoke test
versioning/CHANGELOG.md                  工程版本更新日志
versioning/VERSION.md                    当前版本与版本规则
docs/product/CHANGELOG.md                产品更新日志
docs/product/mvp-scope.md                当前 MVP 范围与验收标准
docs/product/module-boundary.md          当前模块边界
```

## 3. 当前产品 API

前端主接口：

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

账号与协同接口：

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

## 4. 账号角色

```text
老板账号：看全部店群、完整报告、任务流转、复核结果，可以下发任务。
店群总管账号：接收老板任务，拆分给运营，复核运营提交结果。
运营账号：只处理自己的任务，提交处理说明。
数据 / 财务账号：查看 ERP / CRM 报表和财务口径，不直接处理运营任务。
只读观察账号：只看总览、报告和日志，不创建、派发、提交或复核任务。
```

## 5. 本地运行

```bash
cp .env.example .env
bash scripts/start_server.sh
```

本地访问：

```text
http://127.0.0.1:3000
```

健康检查：

```bash
curl http://127.0.0.1:3000/api/health
curl http://127.0.0.1:3000/api/modules/dashboard
curl http://127.0.0.1:3000/api/accounts
```

本地脚本验收：

```bash
python scripts/check_version_governance.py
python scripts/smoke_test_runtime.py
python scripts/smoke_test_api.py
```

## 6. 服务器部署

服务器推荐结构：

```text
公网用户 → 80/443 → Nginx → 127.0.0.1:3000 → FastAPI
```

安全组建议：

```text
80 / 443：公网访问
22：仅限你的固定公网 IP
3000：不要对公网开放
```

一键部署：

```bash
sudo apt-get update
sudo apt-get install -y git

git clone https://github.com/yu5-520/AI-e-commerce-assistant.git /opt/ai-ecommerce-assistant
cd /opt/ai-ecommerce-assistant
sudo bash scripts/deploy_server.sh
```

详细部署说明：

```text
docs/server-deploy.md
```

## 7. 当前边界

```text
不接真实店铺后台
不接真实企业 SSO
不保存真实客户隐私
不自动改价
不自动投放
不自动报名活动
不自动群发客户
不自动处理退款
只生成经营判断、动作草案、详细报告、派发任务和复核记录
```

## 8. 清理规则

main 分支只保留当前产品主线。

```text
旧模板、旧 demo、旧 Agent、旧兼容接口、旧运行命令不放在当前主分支。
需要回看历史版本时，从 Git commit 历史查找。
```

## 9. 版本记录规则

```text
结构级变更：更新 versioning/CHANGELOG.md 和 versioning/VERSION.md
产品主链路 / 页面 / API 边界变化：更新 docs/product/CHANGELOG.md
重大产品取舍：补充 docs/product/product-decision-log.md
结构清理 / 删除旧链路：补充 docs/product/product-structure-cleanup-log.md
测试脚本：必须跟随当前 API 主线同步
```
