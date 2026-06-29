# AI ERP 企业级电商经营 SaaS 底座

当前基线：**V12.9.0 任务生命周期状态机统一写入口版**。

V12.9.0 保留 V12.8.3 的任务卡动作与聚合详情收口，本版重点修复“接收任务点了没用、状态不进入下一阶段”的主链路断点。接收、提交、复核、复盘完成和RAG候选生成必须统一走 `task_lifecycle_state_machine_service`，同一个 primary `task_id` 贯穿任务列表、任务详情、生命周期事件、SQLite镜像和前端任务缓存。

## 当前执行入口

```text
前端唯一入口：web_demo/
后端唯一入口：src/api/main.py
版本主文件：VERSION.md + versioning/VERSION.md
运行态数据库：SQLite Demo runtime
部署脚本：scripts/deploy_fast.sh / scripts/deploy_atomic.sh
```

## 当前主链路

```text
报表 / 接口数据导入
→ 报表布局 Agent / 指标事实表 / 数据缺口池
→ 首份报表 baseline_snapshot，只建基线
→ 两份报表才允许环比经营任务
→ risk_task_service 生成红线任务 + ROI/GMV经营任务
→ rag_business_memory_service 读取公司基线 + approved/effective RAG经验卡
→ action_impact_estimation_service 系统生成保守/正常/乐观影响估算
→ action_authorization_gate_service 按预算权限、保守下限、公司基线、治理权重判断审批
→ task_cluster_service 生成真实后端聚合任务
→ /api/modules/todo 返回带 taskLifecycle 和 primaryTaskAction 的真实任务池
→ task_lifecycle_state_machine_service 统一写入接收、提交、复核、复盘和RAG候选
→ task_report_service 从同一生命周期投影生成中文详情报告
→ task_state_machine_service 镜像任务、事件、日志到 SQLite
```

## V12.9.0 硬规则

```text
接收任务必须走 task_lifecycle_state_machine_service。
接收成功后 status 必须变成“处理中”。
接收成功后 lifecycleStage 必须变成 accepted。
接收成功后必须写 operator_accepted 事件。
后端必须返回同一个 task_id 的最新 task projection。
前端接收后必须先 upsert 返回 task，再 refreshTaskState。
提交任务必须走 task_lifecycle_state_machine_service。
无复核任务提交后进入“等待自动复盘”。
需复核任务提交后进入“待复核”。
复核只属于管理任务视角。
复盘由系统自动生成周期，不作为运营按钮。
详情报告必须从生命周期状态机投影读取任务，不得重新拼旧任务结构。
```

## 当前主 API

```text
/                                      web_demo 前端入口
/api/health                            健康检查
/api/modules/todo                      带生命周期和单动作的任务队列来源
/api/modules/todo/lifecycle/summary    任务生命周期统计
/api/modules/todo/{id}/accept          接收任务：写 operator_accepted 事件并进入处理中
/api/modules/todo/{id}/submit          提交材料：进入待复核或等待自动复盘
/api/modules/todo/{id}/review          复核：通过后生成自动复盘周期，退回后补充材料
/api/modules/todo/{id}/recap/complete  完成复盘并生成RAG候选
/api/modules/task-reports/tasks/{id}   生命周期详情报告
/api/system/runtime-diagnostics        运行态诊断
/api/system/reset-runtime-data          清空演示运行态
```

## 部署入口

```bash
bash scripts/deploy_fast.sh
```
