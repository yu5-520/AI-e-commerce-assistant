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

### 文件上传链路

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
→ operating_cadence_task_service ROI/GMV主轴 + 上传频率 + 3/7/14/30/90 天节奏任务
→ task_evidence_gate_service 按 metric_scope 取证
→ import_diagnostics_service.import_diagnostics
→ v116_import_closed_loop_service
→ dashboard / operating-unit / product / todo / log 反查
```

### 数据源同步链路

```text
web_demo/modules/report/page.js
→ AppApi.dataSourceConnections()
→ GET /api/data/source-connections
→ src/api/routes/data_source_compat.py
→ data_source_connection_service.list_data_source_connections

web_demo/modules/report/page.js
→ AppApi.syncDataSource(sourceId)
→ POST /api/data/source-connections/{source_id}/sync
→ src/api/routes/data_import.py
→ data_source_connection_service
→ _run_dataset_imports_without_legacy_tasks
→ operating_object_store_service
→ metric_fact_store_service
→ data_gap_event_service
→ trend_signal_service
→ risk_task_service
→ operating_cadence_task_service
→ import_diagnostics_service
→ v116_import_closed_loop_service
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

## 5. ROI/GMV 经营节奏任务链

V12.4.1 后，任务不再平铺所有指标，也不只来自单一基线报警。运营主轴是 ROI 和 GMV。

```text
product_metric_facts
→ operating_cadence_task_service._upload_cadence
→ 3 / 7 / 14 / 30 / 90 天窗口判断
→ ROI + GMV/payment_amount 四象限
→ 高 ROI + 高 GMV：放量承接
→ 高 ROI + 低 GMV：扩流测试
→ 低 ROI + 高 GMV：效率复核
→ 低 ROI + 低 GMV：降投排查
→ 库存 / 流量 / 点击 / 转化 / 退款 / 毛利 / 广告消耗解释原因
→ 红线硬规则：urgent_execution
→ 非红线波动：daily_operating_task / weekly_review_task / candidate_only / report_seed_only
→ task_evidence_gate_service.apply_evidence_gate_to_created_task
→ module_task_service.create_task
→ operating_cadence_signals
→ 日报 / 周报素材
```

边界：

```text
红线由硬规则控制，Agent 不允许降级。
ROI/GMV 是任务优先级主轴。
库存、流量、点击率、转化率、退款率、毛利率、广告消耗是解释指标。
日报/周报基础 = 已生成任务 + 候选任务 + 趋势信号 + 观察项。
日报/周报优先围绕 ROI、GMV、广告消耗组织。
```

## 6. 任务模块链

```text
business_signals_v6
→ risk_task_service.generate_risk_tasks_for_signals
→ risk_task_v66_service 严格红线与风险任务
→ operating_cadence_task_service ROI/GMV经营节奏任务
→ task_evidence_gate_service.evaluate_task_evidence
→ product / traffic_source / store metric_scope 取证
→ module_task_service
→ task_repository_write_service
→ task_state_machine_service
→ web_demo/modules/todo/page.js
```

任务页默认承接高风险、高时效和 daily_operating_task；普通缺口只留在 data_gap_events，不制造前端待办。

## 7. 任务详情 / 报告链

```text
web_demo/modules/task-report/page.js
→ AppApi.taskReport() / candidateReport() / alertReport()
→ /api/modules/task-reports/*
→ src/api/routes/modules/task_report.py
→ task_report_service
→ evidenceGate / metricFacts / cadence / ROI-GMV quadrant / dataVersion
```

## 8. 系统诊断 / 清空运行态链

```text
web_demo/modules/system-status/page.js
→ AppApi.resetRuntimeData()
→ POST /api/system/reset-runtime-data?confirm=true
→ system_service.clear_runtime_data
→ 删除导入行、快照、业务信号、经营节奏信号、任务、日志、经营商品、经营店铺、事实表、缺口池
```

清空后 `operating_cadence_signals` 也必须被清理。

## 9. 账号权限链

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

## 10. SaaS 数据隔离链

```text
Request Headers / Session
→ UserContext
→ ScopedRepositoryBase
→ TaskRepository / ProductionRepository
→ tenant_id + org_id + store scope + deleted_at
```

## 11. LLM / Agent 链

```text
/api/modules/agents
→ /api/llm/generate
→ llm_gateway_service
→ prompt_template_service
→ llm_provider_service
→ llm_trace_service
```

LLM 可降级；LLM 不可用时核心事实、缺口、ROI/GMV节奏任务和证据闸门链路不阻断。
