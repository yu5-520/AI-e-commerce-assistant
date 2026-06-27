# V12.3 部署 Runbook

本文件只保留服务器部署、版本一致性和排障边界，不写长篇架构解释。旧部署说明进入提交历史或 `docs/archive/`，不作为当前部署依据。

## 1. 部署分层

```text
Demo 高频小改：scripts/deploy_fast.sh
阶段轻量发布：scripts/deploy_atomic.sh
客户 / 生产发布：LIGHT_DEPLOY=0 ROUTE_GUARD_MODE=strict RUNTIME_ROUTE_GUARD=strict bash scripts/deploy_atomic.sh
```

当前 Demo 阶段默认使用快速部署，目标是每次小改 30 秒到 2 分钟内完成验证。

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

适合：前端 UI、按钮跳转、字段文案、普通接口字段、普通 service 逻辑和 Demo 高频测试。

## 3. 依赖安装边界

只有 requirements.txt 变化时才设置：

```text
FORCE_INSTALL_REQUIREMENTS=1
```

requirements.txt 没变时，Demo 快速部署禁止反复 pip install。

## 4. 轻量原子部署边界

阶段版本或一整天收口后使用：

```bash
bash scripts/deploy_atomic.sh
```

轻量原子部署继续使用：

```text
/opt/ai-ecommerce-assistant-deploy/releases
/opt/ai-ecommerce-assistant-deploy/current
/opt/ai-ecommerce-assistant-deploy/shared/.venv
```

## 5. 生产部署边界

客户环境或多人使用环境再开启严格发布：

```text
LIGHT_DEPLOY=0
ROUTE_GUARD_MODE=strict
RUNTIME_ROUTE_GUARD=strict
```

生产默认禁止前端 mock 身份；ECS Demo 只有明确设置 `DEMO_ACCOUNT_SWITCH=true` 时才允许账号切换验证。

## 6. 部署前检查项

```text
VERSION.md
versioning/VERSION.md
src/api/main.py:API_VERSION
src/api/routes/health.py:API_VERSION
web_demo/index.html?v=12.3.0
scripts/verify_release.py
scripts/check_repo_hygiene.py
docs/API_CONTRACT.md
docs/MODULE_CHAIN.md
docs/DEPLOYMENT_RUNBOOK.md
```

## 7. 部署后验收接口

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/data/source-connections
curl http://127.0.0.1:8000/api/data/metric-facts/summary
curl http://127.0.0.1:8000/api/data/data-gaps/summary
curl http://127.0.0.1:8000/api/data/import-diagnostics
curl http://127.0.0.1:8000/api/system/runtime-diagnostics
```

重点验收：

```text
/api/health 返回 12.3.0。
web_demo/index.html 只出现 12.3.0 资源版本。
GET /api/data/source-connections 不返回 404。
账号切换在 Demo 开关开启时不返回 403。
导入真实 ERA 表后，importDiagnostics.layoutMode = sheet_block_fact_gap_staging。
商品页事实表未命中显示“未识别”，不显示 0，不读对象缓存。
任务 evidenceGate 返回 metricScope / requiredFactTables / forbiddenCrossScope。
```

## 8. Demo 数据清理

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

## 9. 禁止事项

```text
不要 fetch 失败后继续 reset。
不要在 ECS 手动 patch src/ 后不提交 GitHub。
不要让前端静态文件和后端 app.version 来自不同提交。
不要让 VERSION.md 和 versioning/VERSION.md 不一致。
不要让 docs/API_CONTRACT.md 记录不存在的 FastAPI 路由。
不要把 frontend/ 当作当前前端入口。
不要把旧 V1-V11 文档当作当前架构依据。
不要用对象缓存给商品页经营指标托底。
不要用 traffic_source ROI 覆盖 product ROI。
```

## 10. 当前推荐节奏

```text
每次小改：bash scripts/deploy_fast.sh
阶段收口：bash scripts/deploy_atomic.sh
客户部署：LIGHT_DEPLOY=0 严格发布
```
