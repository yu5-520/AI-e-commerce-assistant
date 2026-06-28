# V12.8 部署 Runbook

本文件只保留服务器部署、版本一致性和排障边界。V12.8 的核心验收是：任务生命周期从生成任务到RAG候选闭环，`/api/modules/todo` 返回 `taskLifecycle`，复核通过后生成自动复盘周期，复盘完成后生成RAG候选。

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
4. 检查 VERSION.md / versioning/VERSION.md / app.version / health.API_VERSION / 前端资源版本。
5. 执行 scripts/check_repo_hygiene.py 仓库卫生检查。
6. systemd 指回 /opt/ai-ecommerce-assistant。
7. 写入 Demo 环境变量：APP_ENV=demo、STRICT_DATA_SCOPE=false、DEMO_ACCOUNT_SWITCH=true。
8. 重启后端和 nginx。
9. /api/health 版本通过后完成。
```

## 3. 部署前检查项

```text
VERSION.md
versioning/VERSION.md
src/api/main.py:API_VERSION
src/api/routes/health.py:API_VERSION
web_demo/index.html?v=12.8.0
src/services/risk_task_service.py
src/services/module_task_service.py
src/services/task_lifecycle_orchestrator_service.py
src/services/task_recap_scheduler_service.py
src/services/rag_feedback_loop_service.py
src/services/task_evidence_service.py
src/services/rag_business_memory_service.py
src/api/routes/modules/todo.py
scripts/verify_release.py
scripts/check_repo_hygiene.py
docs/MODULE_CHAIN.md
docs/DEPLOYMENT_RUNBOOK.md
```

## 4. 部署后验收接口

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/modules/todo
curl http://127.0.0.1:8000/api/modules/todo/lifecycle/summary
curl http://127.0.0.1:8000/api/data/import-diagnostics
curl http://127.0.0.1:8000/api/system/runtime-diagnostics
```

重点验收：

```text
/api/health 返回 12.8.0。
web_demo/index.html 只出现 12.8.0 资源版本。
GET /api/modules/todo 返回 taskLifecycleSync。
每个可见任务带 taskLifecycle.stage / nextExpected / recapCycles。
接收任务后 stage = accepted。
提交处理材料后 stage = evidence_submitted。
主管复核通过后 stage = recap_scheduled，并生成 recapCycles。
POST /api/modules/todo/{task_id}/recap/complete 后生成 autoRecapResult 和 ragCandidate。
rag_business_memory_service 只召回 approved/effective 经验卡，不召回 pending_review 草案。
```

## 5. Demo 数据清理

清空的是全运行态，不只是导入行。清空范围包括：workflow_runs、execution_logs、import_records、approval_records、task_status、task_assignments、task_submissions、task_reviews、report_records、data_snapshots、metric_snapshots、business_signals_v6、operating_cadence_signals、alert_events、imported_report_rows、operating_products、operating_stores、product_metric_facts、store_metric_facts、traffic_source_facts、data_gap_events。

账号、角色、权限和基础店铺配置必须保留。

## 6. 禁止事项

```text
不要让运营手填ROI/GMV/销量预测。
不要让 pending_review 的RAG草案直接增强任务生成。
不要让任务复核通过后只写日志而不生成复盘周期。
不要让复盘候选和RAG候选脱离原 task_id。
不要让复盘结束后跳过人工审核直接进入 approved RAG。
```
