# V12.5 部署 Runbook

本文件只保留服务器部署、版本一致性和排障边界。V12.5 的核心验收是：首份报表只建基线，非红线 ROI/GMV 经营任务必须有可比报表；总览和任务栏必须共用 `/api/modules/todo` 后端任务源。

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
web_demo/index.html?v=12.5.0
src/services/risk_task_service.py
src/services/operating_cadence_task_service.py
web_demo/core/api-client.js
web_demo/modules/todo/page.js
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
/api/health 返回 12.5.0。
web_demo/index.html 只出现 12.5.0 资源版本。
GET /api/data/source-connections 不返回 404。
GET /api/modules/todo 返回 tasks / activeTasks / counters。
账号切换在 Demo 开关开启时不返回 403。
导入真实 ERA 表后，importDiagnostics.layoutMode = sheet_block_fact_gap_staging。
商品页事实表未命中显示“未识别”，不显示 0，不读对象缓存。
riskTaskSync.mode = v12_5_baseline_first_redline_plus_roi_gmv_operating_task_generation。
riskTaskSync.operatingCadenceSync.baselineMode = true 时，operatingCadenceCreatedTaskCount 只能来自红线任务。
首份报表不得生成 high_roi_low_gmv / 扩流测试 / 加投 / 降投经营测试任务。
两份报表后 comparisonReady = true，才允许 ROI/GMV 环比经营任务。
三份报表或7天窗口后 trendReady = true，才允许趋势任务。
任务页进入时会调用 AppApi.refreshTaskState()，从 /api/modules/todo hydrate AppTaskStore。
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
不要让任务页只读本地空 AppTaskStore。
不要让日报/周报平铺所有指标；日报/周报必须优先围绕 ROI、GMV、广告消耗组织。
```

## 8. 当前推荐节奏

```text
每次小改：bash scripts/deploy_fast.sh
阶段收口：bash scripts/deploy_atomic.sh
客户部署：LIGHT_DEPLOY=0 严格发布
```
