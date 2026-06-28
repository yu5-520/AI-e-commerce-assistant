# MODULE_CHAIN

本文件是 AI 修改仓库时的模块定位地图。只记录 **V12.8.1 当前执行链路**，不记录历史版本流水账。

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
→ metric_fact_store_service.ingest_metric_facts_from_sheet_rows
→ data_gap_event_service.ingest_data_gaps_from_import
→ trend_signal_service.ingest_product_trends
→ risk_task_service.generate_risk_tasks_for_signals
→ operating_cadence_task_service 首份报表基线 + ROI/GMV 对比任务
→ rag_business_memory_service 读取公司基线 + approved/effective RAG经验卡
→ action_impact_estimation_service 系统估算活动/标题/主图/投放影响
→ operating_weight_policy_service 判断权重来源、权重置信度、是否可触发审批
→ action_authorization_gate_service 校验账号权限、动作风险和审批路径
→ task_cluster_service 合并同店铺同动作同原因任务
→ task_lifecycle_orchestrator_service 挂载 taskLifecycle
→ AppApi.refreshTaskState()
→ /api/modules/todo
→ dashboard / operating-unit / product / todo / log 反查
```

## 3. 任务生命周期闭环链

```text
module_task_service.create_task
→ task_lifecycle_orchestrator_service.generated
→ /api/modules/todo/{task_id}/accept
→ task_lifecycle_orchestrator_service.accepted
→ /api/modules/todo/{task_id}/submit-evidence 或 /submit
→ task_lifecycle_orchestrator_service.evidence_submitted
→ /api/modules/todo/{task_id}/review-evidence 或 /review
→ task_lifecycle_orchestrator_service.manager_reviewed
→ task_recap_scheduler_service.schedule_recap_cycles
→ /api/modules/todo/{task_id}/recap/complete
→ task_recap_scheduler_service.complete_recap_cycle
→ rag_feedback_loop_service.build_rag_candidate_from_recap
→ experience_memory_service.draft_experience_from_task
→ 人工审核 approved
→ rag_business_memory_service 下次任务生成召回 approved/effective 经验卡
```

生命周期阶段：

```text
generated
accepted
evidence_submitted
manager_reviewed
recap_scheduled
recap_completed
rag_candidate_created
rag_approved
```

## 4. 前端任务契约链

```text
web_demo/core/api-client.js
→ AppApi.todo()
→ GET /api/modules/todo
→ AppApi.lifecycleSummary()
→ GET /api/modules/todo/lifecycle/summary
→ AppApi.completeRecapTodo(taskId, body)
→ POST /api/modules/todo/{task_id}/recap/complete
→ web_demo/modules/todo/page.js
→ 只展示后端真实任务，不做前端二次聚合
→ web_demo/modules/task-report/page.js
→ 展示 taskLifecycle / recapCycles / ragCandidate
```

禁止：`todo/page.js` 出现本地 `clusterTasks()` 或写死旧 `12.7.1` 聚合版本。

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

事实表未命中显示“未识别”，不能显示 0，不能回读对象缓存。

## 6. 基线优先任务链

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

## 7. 权重置信度链

```text
经营任务 payload
→ operating_weight_policy_service.infer_operating_weight
→ weightLevel / weightConfidence / weightSource / canTriggerApproval
→ report-only markers ignored: 高ROI / 高GMV / 点击率 / 转化率 / 商品生命周期标签 / 首份报表标签
→ explicit governance sources only: RAG配置 / 主管标记 / 老板标记 / 多期历史贡献
→ action_authorization_gate_service.authorize_action
→ auto_execute / manager_approval_required / owner_approval_required
```

## 8. RAG 反馈链

```text
复盘完成结果
→ rag_feedback_loop_service.build_rag_candidate_from_recap
→ experience_memory_service.upsert_case(status=pending_review)
→ 人工审核 approved
→ search_cases(effective_only=True, min_quality=0.7)
→ rag_business_memory_service.approvedExperienceCards
→ 新任务 SOP / 估算 / 权限判断增强
```

边界：pending_review 只做候选，不直接增强任务生成。

## 9. 总览 / 任务栏统一任务源

```text
/api/modules/dashboard
→ todayWorkbench.todayPriorityTasks

web_demo/modules/todo/page.js
→ AppApi.refreshTaskState()
→ GET /api/modules/todo
→ AppTaskStore.hydrate(tasks, events, counters)
→ visibleTaskQueue(activeTasks)
```

任务列表只显示紧急程度、截止时间、店铺、商品、状态、负责人、生命周期阶段和详情入口；完整 SOP、证据链、估算结果、权限判断、自动复盘周期和 RAG 候选放到任务详情页。
