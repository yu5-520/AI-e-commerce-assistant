# MODULE_CHAIN

本文件是 AI 修改仓库时的模块定位地图。只记录当前执行链路，不记录历史版本流水账。

## 0. 当前入口链

```text
web_demo/index.html
→ web_demo/core/router.js
→ web_demo/core/api-client.js
→ src/api/main.py
→ src/api/routes/*
→ src/services/*
→ src/repositories/* 或 src/db/*
```

`web_demo/` 是唯一当前前端入口。`frontend/` 已标记为历史资产，不作为 UI 修改依据。

## 1. 版本一致性链

```text
VERSION.md
→ versioning/VERSION.md
→ src/api/main.py:API_VERSION
→ src/api/routes/health.py:API_VERSION
→ web_demo/index.html?v=x.y.z
→ scripts/verify_release.py
→ scripts/check_repo_hygiene.py
```

## 2. 数据 / 报表导入链

```text
web_demo/modules/report/page.js
→ AppApi.uploadReportFile()
→ POST /api/data/upload/confirm
→ src/api/routes/data_import.py
→ import_adapter_service.parse_upload_file
→ report_profile_agent_service 生成 sheetProfiles[].blocks[]
→ report_schema_service.confirm_report_import(auto_create_tasks=False)
→ operating_object_store_service.upsert_operating_objects_from_import
→ metric_fact_store_service.ingest_metric_facts_from_sheet_rows
→ data_gap_event_service.ingest_data_gaps_from_import
→ trend_signal_service.ingest_product_trends
→ risk_task_service.generate_risk_tasks_for_signals
→ risk_task_v66_service 红线 / 证据闸门任务
→ operating_cadence_task_service 首份报表基线 + ROI/GMV 对比任务
→ module_task_service.apply_v126_task_governance
→ rag_business_memory_service 读取 RAG 公司基线和历史经营记忆
→ action_impact_estimation_service 系统估算活动/标题/主图/投放影响
→ operating_weight_policy_service 判断权重来源、权重置信度、是否可触发审批
→ action_authorization_gate_service 校验账号权限、动作风险和审批路径
→ task_evidence_gate_service 按 metric_scope 取证
→ import_diagnostics_service.import_diagnostics
→ AppApi.refreshTaskState()
→ /api/modules/todo
→ dashboard / operating-unit / product / todo / log 反查
```

## 3. 商品档案链

```text
web_demo/modules/product/page.js
→ AppApi.product({storeId, storeName})
→ GET /api/modules/product
→ src/api/routes/modules/product.py
→ operating_object_store_service 读取身份主档
→ product_archive_detail_service 读取事实表
→ product_metric_facts / traffic_source_facts / store_metric_facts
```

事实表未命中显示“未识别”，不能显示 0，不能回读对象缓存。

## 4. 基线优先任务链

```text
product_metric_facts
→ operating_cadence_task_service._upload_cadence
→ baselineMode / comparisonReady / trendReady
→ 1份报表：baseline_snapshot
→ 2份报表：允许环比 ROI/GMV 经营任务
→ 3份报表或7天窗口：允许 3/7/14/30/90 天趋势任务
→ 红线硬规则：urgent_execution
→ 非红线波动：daily_operating_task / weekly_review_task / candidate_only / report_seed_only
→ module_task_service.create_task
→ operating_cadence_signals
→ 日报 / 周报素材
```

## 5. V12.7 权重置信度链

```text
经营任务 payload
→ operating_weight_policy_service.infer_operating_weight
→ weightLevel / weightConfidence / weightSource / canTriggerApproval
→ report-only markers ignored: 高ROI / 高GMV / 点击率 / 转化率 / 商品生命周期标签 / 首份报表标签
→ explicit governance sources only: RAG配置 / 主管标记 / 老板标记 / 多期历史贡献
→ action_authorization_gate_service.authorize_action
→ auto_execute / manager_approval_required / owner_approval_required
```

边界：

```text
经营表现不等于权限权重。
任务优先级不等于商品权重。
首份报表不能直接判高权重。
高权重审批必须有明确 weightSource 和足够 weightConfidence。
```

## 6. V12.7 经营动作权限闸门

```text
经营任务 payload
→ module_task_service.normalize_task
→ apply_v126_task_governance
→ rag_business_memory_service.business_memory_context
→ action_impact_estimation_service.estimate_action_impact
→ operating_weight_policy_service.infer_operating_weight
→ action_authorization_gate_service.authorize_action
→ auto_execute / manager_approval_required / owner_approval_required
```

## 7. 总览 / 任务栏统一任务源

```text
/api/modules/dashboard
→ todayWorkbench.todayPriorityTasks

web_demo/modules/todo/page.js
→ AppApi.refreshTaskState()
→ GET /api/modules/todo
→ AppTaskStore.hydrate(tasks, events, counters)
→ visibleTaskQueue(activeTasks)
```

任务列表只显示紧急程度、截止时间、店铺、商品、状态、负责人和详情入口；完整 SOP、证据链、估算结果、权限判断放到任务详情页。

## 8. 经营页入口链

```text
web_demo/modules/operating-unit/page.js
→ 店铺卡片永远保留“查看商品”
→ 有任务时追加“查看任务”
→ 不能因为生成任务替换商品入口
```

## 9. 任务详情 / 报告链

```text
web_demo/core/task-actions.js
→ AppTaskActions.openTaskReport()
→ web_demo/modules/task-report/page.js
→ AppApi.taskReport() / candidateReport() / alertReport()
→ /api/modules/task-reports/*
→ src/api/routes/modules/task_report.py
→ task_report_service
→ evidenceGate / metricFacts / cadence / ROI-GMV quadrant / actionAuthorization / actionImpactEstimate / ragBusinessMemory / objectWeight
```

## 10. 系统诊断 / 清空运行态链

```text
web_demo/modules/system-status/page.js
→ AppApi.resetRuntimeData()
→ POST /api/system/reset-runtime-data?confirm=true
→ system_service.clear_runtime_data
→ 删除导入行、快照、业务信号、经营节奏信号、任务、日志、经营商品、经营店铺、事实表、缺口池
```

清空后 `operating_cadence_signals` 也必须被清理。
