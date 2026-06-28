# V12.6 部署 Runbook

本文件只保留服务器部署、版本一致性和排障边界。V12.6 的核心验收是：首份报表仍只建基线；经营任务生成后必须带 `actionAuthorization`、`actionImpactEstimate`、`ragBusinessMemory`，并按账号权限、店铺权重、商品权重和系统保守估算下限进入自动执行或主管/老板确认。

## 1. 部署分层

```text
Demo 高频小改：scripts/deploy_fast.sh
阶段轻量发布：scripts/deploy_atomic.sh
客户 / 生产发布：LIGHT_DEPLOY=0 ROUTE_GUARD_MODE=strict RUNTIME_ROUTE_GUARD=strict bash scripts/deploy_atomic.sh
```

## 2. Demo 快速部署行为

```text
1. 拉取 GitHub 最新 main。
2. fetch 失败立即停止，不 reset 到旧缓存。
3. reset bootstrap 仓库到 origin/main。
4. 不创建 release。
5. 不重建 venv。
6. 默认不安装依赖。
7. 检查 VERSION.md / versioning/VERSION.md / app.version / health.API_VERSION / 前端资源版本。
8. 执行 scripts/check_repo_hygiene.py 仓库卫生检查。
9. systemd 指回 /opt/ai-ecommerce-assistant。
10. 写入 Demo 环境变量：APP_ENV=demo、STRICT_DATA_SCOPE=false、DEMO_ACCOUNT_SWITCH=true。
11. 重启后端和 nginx。
12. /api/health 版本通过后完成。
```

## 3. 依赖安装边界

只有 requirements.txt 变化时才设置：

```text
FORCE_INSTALL_REQUIREMENTS=1
```

requirements.txt 没变时，Demo 快速部署禁止反复 pip install。

## 4. 部署前检查项

```text
VERSION.md
versioning/VERSION.md
src/api/main.py:API_VERSION
src/api/routes/health.py:API_VERSION
web_demo/index.html?v=12.6.0
src/services/risk_task_service.py
src/services/module_task_service.py
src/services/action_authorization_gate_service.py
src/services/action_impact_estimation_service.py
src/services/rag_business_memory_service.py
web_demo/core/api-client.js
web_demo/core/task-actions.js
web_demo/modules/todo/page.js
web_demo/modules/operating-unit/page.js
scripts/verify_release.py
scripts/check_repo_hygiene.py
docs/API_CONTRACT.md
docs/MODULE_CHAIN.md
docs/DEPLOYMENT_RUNBOOK.md
```

## 5. 部署后验收接口

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/data/source-connections
curl http://127.0.0.1:8000/api/data/metric-facts/summary
curl http://127.0.0.1:8000/api/data/data-gaps/summary
curl http://127.0.0.1:8000/api/data/import-diagnostics
curl http://127.0.0.1:8000/api/modules/todo
curl http://127.0.0.1:8000/api/system/runtime-diagnostics
```

重点验收：

```text
/api/health 返回 12.6.0。
web_demo/index.html 只出现 12.6.0 资源版本。
GET /api/data/source-connections 不返回 404。
GET /api/modules/todo 返回 tasks / activeTasks / counters。
任务对象带 actionAuthorization / actionImpactEstimate / ragBusinessMemory。
任务 actionAuthorization.decision 可为 auto_execute / manager_approval_required / owner_approval_required。
活动任务中，运营只补充活动事实和竞品事实，系统估算 ROI/GMV/毛利/库存影响。
标题/主图测试中，中权重对象直接生成运营执行任务，高权重对象进入主管确认。
任务列表只显示紧急程度、截止时间、店铺、商品、状态和详情入口。
任务详情按钮通过 task-report 打开，不依赖缺失的全局对象。
经营页店铺卡片始终保留“查看商品”，有任务时追加“查看任务”。
```

## 6. Demo 数据清理

清空的是全运行态，不只是导入行。清空范围包括：

```text
workflow_runs
execution_logs
import_records
approval_records
task_status
task_assignments
task_submissions
task_reviews
report_records
data_snapshots
metric_snapshots
business_signals_v6
operating_cadence_signals
alert_events
imported_report_rows
operating_products
operating_stores
product_metric_facts
store_metric_facts
traffic_source_facts
data_gap_events
```

账号、角色、权限和基础店铺配置必须保留。

## 7. 禁止事项

```text
不要 fetch 失败后继续 reset。
不要在 ECS 手动 patch src/ 后不提交 GitHub。
不要让前端静态文件和后端 app.version 来自不同提交。
不要让 VERSION.md 和 versioning/VERSION.md 不一致。
不要让 docs/API_CONTRACT.md 记录不存在的 FastAPI 路由。
不要把 frontend/ 当作当前前端入口。
不要用对象缓存给商品页经营指标托底。
不要用 traffic_source ROI 覆盖 product ROI。
不要让第一份报表生成扩流、加投、降投等经营测试任务。
不要让运营填写预测 ROI、GMV、销量、库存消耗、毛利率。
不要让高权重店铺/商品的标题、主图、预算、价格、主推位动作绕过主管确认。
不要让任务页只读本地空 AppTaskStore。
```

## 8. 当前推荐节奏

```text
每次小改：bash scripts/deploy_fast.sh
阶段收口：bash scripts/deploy_atomic.sh
客户部署：LIGHT_DEPLOY=0 严格发布
```
