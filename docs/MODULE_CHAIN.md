# MODULE_CHAIN

本文件是 AI 修改仓库时的模块定位地图。只记录当前主架构链路，不记录历史版本。

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

适用问题：页面打不开、切页崩溃、接口 fallback、缓存版本混乱、前后端入口不一致。

## 1. 总览模块链

```text
web_demo/modules/dashboard/page.js
→ AppApi.dashboard()
→ GET /api/modules/dashboard
→ src/api/routes/modules/dashboard.py
→ dashboard / report / task projection services
```

关联模块：数据、经营、任务、日志。

验收点：报表导入后，总览必须同步刷新最新任务、高风险事项、最新报表结果、待复核事项和今日完成进度。

## 2. 数据 / 报表导入模块链

### 2.1 JSON rows 旧链路

```text
web_demo/modules/report/page.js
→ AppApi.previewReportRows()
→ POST /api/data/preview

web_demo/modules/report/page.js
→ AppApi.confirmReportImport()
→ POST /api/data/import/confirm
→ src/api/routes/data_import.py
→ report_schema_service
→ trend_signal_service
→ risk_task_service
→ v104_import_task_sync_service
→ v107_operating_profile_service
→ v108_tag_change_task_service
```

### 2.2 Excel / CSV / JSON 文件上传链路

```text
web_demo/modules/report/page.js
→ AppApi.uploadReportFile()
→ POST /api/data/upload/confirm
→ src/api/routes/data_import.py
→ import_adapter_service
→ Excel / CSV / JSON parser
→ Sheet 识别
→ 原始事实 rows
→ report_schema_service
→ trend_signal_service
→ risk_task_service
→ v104_import_task_sync_service
→ v107_operating_profile_service
→ v108_tag_change_task_service
```

边界：`import_adapter_service` 只能做文件读取、Sheet 识别、字段读取和单元格格式标准化，不能提前写风险判断、任务线索、售后归因或经营建议。

关联模块：总览、经营、任务、日志、趋势、RAG。

验收点：确认导入后必须返回导入结果、上传元信息、趋势同步、风险任务同步、经营档案、标签变化任务同步，并触发前端刷新。

## 3. 经营模块链

```text
web_demo/modules/operating-unit/page.js
→ AppApi.operatingUnit()
→ GET /api/modules/operating-unit
→ src/api/routes/modules/operating_unit.py

商品 / 竞品 / 上新 / 流量：
web_demo/modules/operating-unit/page.js
→ AppApi.product() / competitor() / listing() / traffic()
→ /api/modules/product | competitor | listing | traffic
→ src/api/routes/modules/product.py 等
→ module_projection_service
→ report_alert_service
→ module_task_service
```

关联模块：数据、任务、Agent、趋势。

验收点：经营模块只展示当前账号可见店铺和商品；达到预警条件的经营项必须能生成任务候选或进入统一任务池。

## 4. 任务模块链

```text
web_demo/modules/todo/page.js
→ AppApi.todo()
→ GET /api/modules/todo
→ src/api/routes/modules/todo.py
→ module_task_service
→ v105_cross_account_flow_service
→ v106_task_action_simplifier
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

验收点：同一 task_id 必须能投射老板、总管、运营三种角色视图；任务完成后，相关模块中对应任务状态必须同步消失或变更。

## 5. 任务详情 / 报告模块链

```text
web_demo/modules/task-report/page.js
→ AppApi.taskReport() / candidateReport() / alertReport()
→ /api/modules/task-reports/*
→ src/api/routes/modules/task_report.py
→ task report / agent report services
```

关联模块：任务、经营、数据、Agent。

验收点：任务详情必须说明为什么预警、关联了哪些数据版本、建议怎么处理、需要什么证据。

## 6. 账号权限模块链

```text
web_demo/modules/account/page.js
→ /api/accounts
→ src/api/routes/accounts.py
→ account_service
→ src/core/context.py
→ src/repositories/scoped_repository.py
```

验收点：老板可见全局；总管可见经营单元；运营只可见分配店铺；店铺归属修改必须进入权限和迁移链路。

## 7. SaaS 数据隔离链

```text
Request Headers / Session
→ UserContext
→ ScopedRepositoryBase
→ TaskRepository / ProductionRepository
→ tenant_id + org_id + store scope + deleted_at
```

验收点：任何业务查询不得绕过 UserContext 和数据范围过滤。

## 8. LLM / Agent 模块链

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

## 9. 数据库迁移链

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
