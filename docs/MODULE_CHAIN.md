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
→ action_authorization_gate_service 校验账号权限、店铺权重、商品权重、动作风险
→ task_evidence_gate_service 按 metric_scope 取证
→ import_diagnostics_service.import_diagnostics
→ AppApi.refreshTaskState()
→ /api/modules/todo
→ dashboard / operating-unit / product / todo / log 反查
```

## 3. 报表布局 Agent 与事实表链

```text
Excel / CSV / JSON
→ sheetRows / sheetMatrices / source_row_index / source_column_map
→ reportProfile.sheetProfiles[].blocks[]
→ block.targetTable + block.metricScope
→ product_metric_facts / store_metric_facts / traffic_source_facts
→ source_block_id / source_row_index / source_column_index / metric_scope / source_block_type
```

验收点：一个 Sheet 可以拆出 product / store / traffic_source / staging 多个区块；staging 区块不能进入商品页事实展示，也不能生成经营任务。

## 4. 商品档案链

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

## 5. 基线优先任务链

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

## 6. V12.6 经营动作权限闸门

```text
经营任务 payload
→ module_task_service.normalize_task
→ apply_v126_task_governance
→ rag_business_memory_service.business_memory_context
→ action_impact_estimation_service.estimate_action_impact
→ action_authorization_gate_service.authorize_action
→ auto_execute / manager_approval_required / owner_approval_required
```

边界：

```text
运营只补充客观事实，不填写ROI、GMV、销量、库存消耗、毛利率预测。
系统生成保守 / 正常 / 乐观估算。
自动确认只看保守估算下限。
高权重店铺/商品的标题、主图、预算、价格、主推位等动作必须走主管/老板确认。
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
→ evidenceGate / metricFacts / cadence / ROI-GMV quadrant / actionAuthorization / actionImpactEstimate / ragBusinessMemory
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

## 11. 账号权限链

```text
web_demo/modules/account/page.js
→ /api/accounts
→ /api/accounts/switch
→ account_service
→ src/core/context.py
→ backend_isolation_service
→ scoped_repository.py
```

ECS Demo 只有 `DEMO_ACCOUNT_SWITCH=true` 时允许切换账号。

## 12. LLM / Agent 链

```text
/api/modules/agents
→ /api/llm/generate
→ llm_gateway_service
→ prompt_template_service
→ llm_provider_service
→ llm_trace_service
```

LLM 可降级；LLM 不可用时核心事实、缺口、ROI/GMV节奏任务、V12.6经营动作权限闸门和证据闸门链路不阻断。
