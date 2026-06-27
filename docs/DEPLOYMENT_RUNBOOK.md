# V11.15 Demo 快速部署 Runbook

本文件只保留服务器部署和排障边界，不写长篇架构解释。

## 1. 部署分层

```text
Demo 快速部署：scripts/deploy_fast.sh
阶段轻量发布：scripts/deploy_atomic.sh
客户 / 生产发布：LIGHT_DEPLOY=0 的完整原子部署
```

当前 Demo 阶段默认使用快速部署，目标是每次小改 30 秒到 2 分钟内完成验证。

## 2. Demo 快速部署行为

```text
1. 拉取 GitHub 最新 main。
2. 拉取失败立即停止，不 reset 到旧缓存。
3. reset bootstrap 仓库到 origin/main。
4. 不创建 release。
5. 不重建 venv。
6. 默认不安装依赖。
7. 检查 VERSION / app.version / health.API_VERSION / 前端资源版本。
8. 执行 scripts/check_repo_hygiene.py 仓库卫生检查。
9. systemd 指回 /opt/ai-ecommerce-assistant。
10. 重启后端。
11. /api/health 版本通过后完成。
```

适合：前端 UI、按钮跳转、字段文案、普通接口字段、普通 service 逻辑和 Demo 高频测试。

## 3. 依赖安装边界

只有 requirements.txt 变化时才设置：

```text
FORCE_INSTALL_REQUIREMENTS=1
```

## 4. 轻量原子部署边界

阶段版本或一整天收口后使用 `scripts/deploy_atomic.sh`。轻量原子部署继续使用：

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

## 6. 快速部署检查项

```text
versioning/VERSION.md
scripts/verify_release.py
scripts/check_repo_hygiene.py
/api/health
/api/system/runtime-diagnostics
systemd 服务状态
后端日志
```

## 7. Demo 数据清理

V11.15 清空的是全运行态，不只是导入行。清空范围包括：

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
```

清空后关键表应为 0：

```text
imported_report_rows
data_snapshots
metric_snapshots
business_signals_v6
operating_products
operating_stores
task_status
alert_events
```

账号、角色、权限和基础店铺配置必须保留。

## 8. 禁止事项

```text
不要 fetch 失败后继续 reset。
不要在 ECS 手动 patch src/ 后不提交 GitHub。
不要让前端静态文件和后端 app.version 来自不同提交。
Demo 小改不要每次走完整原子部署。
requirements.txt 没变不要安装依赖。
清空演示数据不能只删 imported_report_rows，必须删完整派生运行态。
```

## 9. 当前推荐节奏

```text
每次小改：scripts/deploy_fast.sh
阶段收口：scripts/deploy_atomic.sh
客户部署：LIGHT_DEPLOY=0 严格发布
```
