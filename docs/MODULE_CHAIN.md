# MODULE_CHAIN

本文件是 AI 修改仓库时的模块定位地图。当前执行链路为 **V12.9.0 任务生命周期状态机统一写入口**。

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
→ report_profile_agent_service 生成 sheetProfiles[].blocks[]
→ metric_fact_store_service 写 product/store/traffic fact tables
→ risk_task_service.generate_risk_tasks_for_signals
→ operating_cadence_task_service 首份报表基线 + ROI/GMV 对比任务
→ rag_business_memory_service 读取公司基线 + approved/effective RAG经验卡
→ action_impact_estimation_service 系统估算活动/标题/主图/投放影响
→ operating_weight_policy_service 判断权重来源和置信度
→ action_authorization_gate_service 校验预算、基线、权重和审批路径
→ task_cluster_service 合并同店铺同动作同原因任务
→ /api/modules/todo 输出带 taskLifecycle / primaryTaskAction 的任务池
```

## 3. V12.9 任务生命周期唯一写入口

```text
/api/modules/todo/{task_id}/accept
/api/modules/todo/{task_id}/submit
/api/modules/todo/{task_id}/review
/api/modules/todo/{task_id}/recap/complete
→ task_lifecycle_state_machine_service.transition_lifecycle_task
→ module_task_service.update_task
→ task_lifecycle_orchestrator_service.attach_lifecycle / schedule_recap_cycles
→ module_task_service.create_task_event
→ task_state_machine_service.mirror_all
→ project_lifecycle_task
→ 返回最新 task projection
→ web_demo/modules/todo/page.js AppTaskStore.upsert(task)
```

硬规则：接收、提交、复核、复盘完成不能绕过 `task_lifecycle_state_machine_service`。

## 4. 生命周期阶段

```text
generated                 生成任务
accepted                  接收任务
evidence_submitted        提交处理材料
returned                  退回补充
recap_scheduled           生成自动复盘周期
recap_completed           复盘完成
rag_candidate_created     进入RAG候选
rag_approved              RAG增强任务生成
archived                  归档
```

## 5. 前端任务契约链

```text
web_demo/modules/todo/page.js
→ AppApi.refreshTaskState()
→ GET /api/modules/todo
→ 渲染 primaryTaskAction + detailAction
→ 点击接收 / 提交
→ POST /api/modules/todo/{task_id}/accept 或 submit
→ applyTransitionResult(result)
→ AppTaskStore.upsert(result.task)
→ refreshTaskState()
```

禁止：`todo/page.js` 出现本地 `clusterTasks()`、直接渲染 raw `availableActions`、或把复核/复盘按钮放在运营卡片。

## 6. 任务详情链

```text
web_demo/modules/task-report/page.js
→ AppApi.taskReport(taskId)
→ GET /api/modules/task-reports/tasks/{task_id}
→ task_report_service.get_task_report
→ task_lifecycle_state_machine_service.get_lifecycle_task_projection
→ 输出 affectedProducts / taskLifecycle / actionAuthorization / recapCycles / nextStep
```

详情报告必须从生命周期状态机投影读取任务，不得重新拼旧任务结构。

## 7. 商品档案链

```text
web_demo/modules/product/page.js
→ AppApi.product({storeId, storeName})
→ GET /api/modules/product
→ operating_object_store_service 读取身份主档
→ product_archive_detail_service 读取事实表
→ product_metric_facts / traffic_source_facts / store_metric_facts
```

事实表未命中显示“未识别”，不能显示 0，不能回读对象缓存。
