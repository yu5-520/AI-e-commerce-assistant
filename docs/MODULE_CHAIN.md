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

验收点：版本不一致时禁止部署；不能出现 main.py 是新版本、health、VERSION 或前端资源仍是旧版本的半更新状态。

## 2. 数据 / 报表导入链

### 2.1 文件上传链路

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
→ task_evidence_gate_service 按 metric_scope 取证
→ import_diagnostics_service.import_diagnostics
→ v116_import_closed_loop_service
→ dashboard / operating-unit / product / todo / log 反查
```

### 2.2 数据源同步链路

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
→ import_diagnostics_service
→ v116_import_closed_loop_service
```

### 2.3 JSON rows 链路

```text
web_demo/modules/report/page.js
→ AppApi.confirmReportImport() / AppApi.importReportRows()
→ POST /api/data/import/confirm 或 /api/data/import/report
→ src/api/routes/data_import.py
→ report_schema_service / report_alert_service
→ operating_object_store_service
→ metric_fact_store_service
→ data_gap_event_service
→ trend_signal_service
→ risk_task_service
→ import_diagnostics_service
```

边界：导入适配器只能做文件读取、Sheet/Block 识别、字段读取和单元格标准化，不能提前写风险判断、售后归因或经营建议。

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

## 4. 经营对象主档链

```text
报表 rows / blockRows
→ operating_object_store_service.ensure_operating_object_tables
→ operating_products / operating_stores
→ 只保留身份定位、权限归属和来源坐标
→ list_operating_products(user_id)
→ list_operating_stores(user_id)
→ operating_object_summary(user_id)
```

核心规则：

```text
上传账号决定正常报表导入归属。
新店铺直接创建并归属上传账号。
商品继承店铺归属。
任务继承商品 / 店铺归属。
经营指标不能写入 operating_products / operating_stores 缓存。
```

## 5. 商品档案链

```text
web_demo/modules/product/page.js
→ AppApi.product({storeId, storeName})
→ GET /api/modules/product
→ src/api/routes/modules/product.py
→ operating_object_store_service 读取身份主档
→ product_archive_detail_service 读取事实表
→ product_metric_facts / traffic_source_facts / store_metric_facts
```

验收点：商品页只展示商品定位、指标事实、流量来源、任务历史摘要。事实表未命中显示“未识别”，不能显示 0，不能回读对象缓存。

## 6. 经营模块链

```text
web_demo/modules/operating-unit/page.js
→ AppApi.operatingUnit()
→ GET /api/modules/operating-unit
→ src/api/routes/modules/operating_unit.py
→ operating_object_store_service
→ module_projection_service
→ report_alert_service
→ module_task_service
→ runtime residue fail-closed
```

经营对象入口：

```text
商品档案：operating-unit → business-products → product/page.js → AppApi.product({storeId, storeName})
竞品信号：operating-unit → business-competitors → competitor/page.js
上新测试：operating-unit → business-listing → listing/page.js
流量趋势：operating-unit → business-traffic → traffic/page.js
```

验收点：经营模块只展示当前账号可见店铺和商品；源数据为 0 但派生运行态残留时返回 dirty_runtime_residue，不聚合旧对象。

## 7. 任务模块链

```text
business_signals_v6
→ risk_task_service.generate_risk_tasks_for_signals
→ task_evidence_gate_service.evaluate_task_evidence
→ product / traffic_source / store metric_scope 取证
→ module_task_service
→ task_repository_write_service
→ task_state_machine_service
→ TaskRepository
→ web_demo/modules/todo/page.js
```

动作链：

```text
派发 / 拆分 → manager_assigned
接收 → operator_accepted
提交 → operator_submitted
复核 → manager_approved / manager_returned
完成 → task_completed
写入复盘 → task_written_to_recap
```

验收点：任务页默认只展示高风险 / 高时效的执行队列；普通缺口只留在 data_gap_events，不能制造前端待办。

## 8. 任务详情 / 报告链

```text
web_demo/modules/task-report/page.js
→ AppApi.taskReport() / candidateReport() / alertReport()
→ /api/modules/task-reports/*
→ src/api/routes/modules/task_report.py
→ task_report_service
→ report_alert_service
→ evidenceGate / metricFacts / dataVersion
```

验收点：任务详情必须说明为什么预警、关联哪些数据版本、缺少哪些证据、建议怎么处理。只要任务进入执行队列，详情页必须能打开。

## 9. 系统诊断 / 清空运行态链

```text
web_demo/modules/system-status/page.js
→ AppApi.resetRuntimeData()
→ POST /api/system/reset-runtime-data?confirm=true
→ src/api/routes/system.py
→ system_service.clear_runtime_data
→ 删除导入行、快照、业务信号、任务、日志、经营商品、经营店铺、事实表、缺口池
→ 保留账号、角色、权限、基础店铺配置
```

验收点：清空后 imported_report_rows、data_snapshots、metric_snapshots、business_signals_v6、operating_products、operating_stores、product_metric_facts、store_metric_facts、traffic_source_facts、data_gap_events、task_status、alert_events 都应为 0。

## 10. 账号权限链

```text
web_demo/modules/account/page.js
→ /api/accounts
→ /api/accounts/switch
→ src/api/routes/accounts.py
→ account_service
→ src/core/context.py
→ backend_isolation_service
→ scoped_repository.py
```

验收点：老板可见全局；总管可见经营单元；运营只可见分配店铺。生产默认禁止 mock 身份；ECS Demo 只有 `DEMO_ACCOUNT_SWITCH=true` 时允许切换账号。

## 11. SaaS 数据隔离链

```text
Request Headers / Session
→ UserContext
→ ScopedRepositoryBase
→ TaskRepository / ProductionRepository
→ tenant_id + org_id + store scope + deleted_at
```

验收点：任何业务查询不得绕过 UserContext 和数据范围过滤。

## 12. LLM / Agent 链

```text
/api/modules/agents
→ /api/llm/generate
→ src/api/routes/llm.py
→ llm_gateway_service
→ prompt_template_service
→ llm_provider_service
→ llm_trace_service
→ trace_audit_service / tech_log_service
```

验收点：LLM 可降级；LLM 不可用时核心任务链路不阻断；所有 LLM 调用必须可追踪。
