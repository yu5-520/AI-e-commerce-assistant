# MODULE_CHAIN

本文件是 AI 修改仓库时的模块定位地图。只记录当前主架构链路，不记录历史版本流水账。

## 0. 全局入口链

```text
web_demo/index.html
→ web_demo/core/router.js
→ web_demo/core/api-client.js
→ src/api/main.py
→ src/api/routes/*
→ src/services/*
→ src/repositories/* 或 src/db/*
```

适用问题：页面打不开、切页崩溃、接口异常、缓存版本混乱、前后端入口不一致。

## 1. 版本一致性链

```text
versioning/VERSION.md
→ src/api/main.py:API_VERSION
→ src/api/routes/health.py:API_VERSION
→ web_demo/index.html?v=x.y.z
→ scripts/verify_release.py
→ scripts/check_repo_hygiene.py
```

验收点：版本不一致时禁止部署；不能出现 main.py 是新版本、health 或 VERSION 仍是旧版本的半更新状态。

## 2. 总览模块链

```text
web_demo/modules/dashboard/page.js
→ AppApi.dashboard()
→ GET /api/modules/dashboard
→ src/api/routes/modules/dashboard.py
→ module_projection_service
→ module_task_service
→ report_alert_service
→ operating_object_store_service
```

验收点：总览展示经营同步结果、今日执行任务、风险事项和复核进度；不展示后端入库明细流水账。

## 3. 数据 / 报表导入模块链

### 3.1 文件上传链路

```text
web_demo/modules/report/page.js
→ AppApi.uploadReportFile()
→ POST /api/data/upload/confirm
→ src/api/routes/data_import.py
→ import_adapter_service
→ Excel / CSV / JSON parser
→ report_schema_service
→ confirm_report_import
→ imported_report_rows / data_snapshots / metric_snapshots / alert_events
→ operating_object_store_service.upsert_operating_objects_from_import
→ trend_signal_service.ingest_product_trends
→ risk_task_service.generate_risk_tasks_for_signals
→ v104_import_task_sync_service
→ v107_operating_profile_service
→ v108_tag_change_task_service
→ v116_import_closed_loop_service
→ dashboard / operating-unit / product / todo / log 反查
```

### 3.2 接口同步链路

```text
web_demo/modules/report/page.js
→ AppApi.syncDataSource(sourceId)
→ POST /api/data/source-connections/{source_id}/sync
→ src/api/routes/data_import.py
→ data_source_connection_service
→ _run_dataset_imports_without_legacy_tasks
→ operating_object_store_service
→ trend_signal_service
→ risk_task_service
→ v116_import_closed_loop_service
```

### 3.3 JSON rows 链路

```text
web_demo/modules/report/page.js
→ AppApi.confirmReportImport() / AppApi.importReportRows()
→ POST /api/data/import/confirm 或 /api/data/import/report
→ src/api/routes/data_import.py
→ report_schema_service / report_alert_service
→ operating_object_store_service
→ trend_signal_service
→ risk_task_service
→ v116_import_closed_loop_service
```

边界：`import_adapter_service` 只能做文件读取、Sheet 识别、字段读取和单元格格式标准化，不能提前写风险判断、任务线索、售后归因或经营建议。

验收点：导入成功必须能反查商品入库数、店铺入库数、业务信号数和可执行任务数；rows > 0 但经营对象为 0 时必须显示失败或阻断，不能假成功。

## 4. 经营对象主档链

```text
报表 rows
→ operating_object_store_service.ensure_operating_object_tables
→ operating_products
→ operating_stores
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
任务不能反向制造商品 / 店铺权限。
```

## 5. 经营模块链

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
商品档案
web_demo/modules/operating-unit/page.js
→ AppRouter.navigate("business-products")
→ web_demo/modules/product/page.js
→ AppApi.product()
→ src/api/routes/modules/product.py

竞品信号
web_demo/modules/operating-unit/page.js
→ AppRouter.navigate("business-competitors")
→ web_demo/modules/competitor/page.js

上新测试
web_demo/modules/operating-unit/page.js
→ AppRouter.navigate("business-listing")
→ web_demo/modules/listing/page.js

流量趋势
web_demo/modules/operating-unit/page.js
→ AppRouter.navigate("business-traffic")
→ web_demo/modules/traffic/page.js
```

验收点：经营模块只展示当前账号可见店铺和商品；源数据为 0 但派生运行态残留时返回 dirty_runtime_residue，不聚合旧对象。

## 6. 任务模块链

```text
web_demo/modules/todo/page.js
→ AppApi.todo()
→ GET /api/modules/todo
→ src/api/routes/modules/todo.py
→ module_task_service
→ risk_task_service
→ task_repository_write_service
→ task_state_machine_service
→ TaskRepository
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

验收点：任务页默认只展示高风险 / 高时效的执行队列；低风险和观察信号不制造前端待办。

## 7. 任务详情 / 报告模块链

```text
web_demo/modules/task-report/page.js
→ AppApi.taskReport() / candidateReport() / alertReport()
→ /api/modules/task-reports/*
→ src/api/routes/modules/task_report.py
→ task_report_service
→ report_alert_service
```

验收点：任务详情必须说明为什么预警、关联了哪些数据版本、建议怎么处理、需要什么证据。只要任务进入执行队列，详情页必须能打开。

## 8. 系统诊断 / 清空演示运行态链

```text
web_demo/modules/system-status/page.js
→ AppApi.resetRuntimeData()
→ POST /api/system/reset-runtime-data?confirm=true
→ src/api/routes/system.py
→ system_service.clear_runtime_data
→ 删除导入行、快照、业务信号、任务、日志、经营商品、经营店铺
→ 保留账号、角色、权限、基础店铺配置
```

验收点：清空后 imported_report_rows、data_snapshots、metric_snapshots、business_signals_v6、operating_products、operating_stores、task_status、alert_events 都应为 0。

## 9. 账号权限模块链

```text
web_demo/modules/account/page.js
→ /api/accounts
→ src/api/routes/accounts.py
→ account_service
→ src/core/context.py
→ src/repositories/scoped_repository.py
```

验收点：老板可见全局；总管可见经营单元；运营只可见分配店铺；店铺归属修改必须进入权限和迁移链路。

## 10. SaaS 数据隔离链

```text
Request Headers / Session
→ UserContext
→ ScopedRepositoryBase
→ TaskRepository / ProductionRepository
→ tenant_id + org_id + store scope + deleted_at
```

验收点：任何业务查询不得绕过 UserContext 和数据范围过滤。Demo 可用 X-Mock-User-Id；生产禁止信任前端 mock 身份。

## 11. LLM / Agent 模块链

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

## 12. 数据库迁移链

```text
SQLite runtime
→ TaskRepository
→ repository_mirror_base_service
→ src/db/models.py
→ src/db/repositories.py
→ Alembic
→ PostgreSQL hybrid / postgres
```

验收点：默认保持 SQLite Demo 稳定；hybrid 模式 mirror 失败不影响 Demo；postgres 主写必须通过 cutover check。
