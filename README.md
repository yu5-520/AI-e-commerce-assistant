# AI ERP 经营单元电商循环系统 MVP

> 一个基于商家 ERP 商品结构识别经营单元的货架电商 AI 工作流原型。系统从商品、库存、订单、退款和客户数据中推断当前经营单元，再生成经营判断、竞品机会、上新建议、流量复盘、待确认动作和经营报告。

## 1. 当前主定位

本仓库当前只保留一条主产品链路：

```text
ERP / CRM Mock 数据
↓
经营单元识别
↓
循环频率策略
↓
商品体检、竞品机会、上新建议、流量复盘
↓
经营循环总控
↓
/api/business/* 产品接口
↓
web_demo/app-v2.js 产品化前端
```

核心原则：

```text
ERP 决定经营单元，经营单元决定类目知识，商品节奏决定循环频率，系统只生成建议、草案、复盘和待确认动作。
```

系统不再保留旧版 demo 入口、旧版前端模板、旧 Agent 链路和旧兼容 API。历史版本由 Git commits 保存，不放在 main 分支干扰当前产品。

## 2. 当前目录职责

```text
src/api/main.py                    FastAPI 唯一入口
src/api/routes/business.py          当前产品业务 API
src/api/routes/approvals.py         确认 / 拒绝动作记录
src/api/routes/data_import.py       Mock 数据校验与导入记录
src/api/routes/health.py            健康检查
src/api/routes/system.py            系统状态与运行数据清理
src/services/business_view_service.py
                                  产品视图包装层
src/workflow/mock_workflow.py       当前 Mock workflow 编排
src/operating_unit/                 ERP 经营单元识别
src/scheduler/                      循环频率策略
src/category/                       经营单元知识档案加载
src/competitor/                     同经营单元竞品比对
src/listing/                        上新增长建议
src/traffic_test/                   流量测试回流
src/operating_loop/                 经营循环总控
src/repositories/                   SQLite / JSONL 记录层
web_demo/index.html                 当前前端入口
web_demo/app-v2.js                  当前前端逻辑
scripts/start_server.sh             本机启动脚本
scripts/deploy_server.sh            服务器部署脚本
scripts/check_version_governance.py 版本治理检查脚本
scripts/smoke_test_runtime.py       当前 workflow smoke test
scripts/smoke_test_api.py           当前产品 API smoke test
deploy/nginx-ai-operating-advisor.conf
                                  Nginx 反向代理配置
versioning/CHANGELOG.md             工程版本更新日志
versioning/VERSION.md               当前版本与版本规则
docs/product/CHANGELOG.md           产品更新日志
docs/product/mvp-scope.md           当前 MVP 范围与验收标准
docs/product/module-boundary.md     当前模块边界
docs/product/product-decision-log.md
                                  产品决策日志
docs/product/product-structure-cleanup-log.md
                                  产品结构清理日志
```

## 3. 当前产品 API

前端只应使用下面这组产品接口：

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

## 4. 本地运行

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
curl http://127.0.0.1:3000/api/business/today
```

本地脚本验收：

```bash
python scripts/check_version_governance.py
python scripts/smoke_test_runtime.py
python scripts/smoke_test_api.py
```

## 5. 服务器部署

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

部署后访问：

```text
http://47.118.29.46
```

详细部署说明：

```text
docs/server-deploy.md
```

## 6. 当前边界

```text
不接真实店铺后台
不自动改价
不自动投放
不自动报名活动
不自动群发客户
不自动处理退款
只生成经营判断、动作草案、复盘报告和待确认事项
```

## 7. 清理规则

main 分支只保留当前产品主线。

```text
旧模板、旧 demo、旧 Agent、旧兼容接口、旧运行命令不放在当前主分支。
需要回看历史版本时，从 Git commit 历史查找。
```

## 8. 版本记录规则

```text
结构级变更：更新 versioning/CHANGELOG.md 和 versioning/VERSION.md
产品主链路 / 页面 / API 边界变化：更新 docs/product/CHANGELOG.md
重大产品取舍：补充 docs/product/product-decision-log.md
结构清理 / 删除旧链路：补充 docs/product/product-structure-cleanup-log.md
测试脚本：必须跟随当前 API 主线同步
```
