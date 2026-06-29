# AI ERP 企业级电商经营 SaaS 底座

当前基线：**V12.9.1 自动接收与幂等生命周期版**。

V12.9.1 保留 V12.9 的任务生命周期状态机，本版修正“接收写了日志但任务卡仍像没进入下一阶段”的断点：运营权限内、无需主管/老板复核的任务生成后自动接收，直接进入 `处理中 / accepted`；人工接收接口保持幂等，任务已经处于处理中或后续阶段时，不重复写接收日志，只返回最新任务投影。状态机也能从 SQLite TaskRepository 读取并回灌任务，避免“列表读Repository，接收写Memory”的断层。

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
→ action_authorization_gate_service 判断是否需要主管/老板复核
→ task_cluster_service 生成真实后端聚合任务
→ /api/modules/todo 读取任务池
→ task_lifecycle_state_machine_service 自动接收权限内任务
→ 前端任务卡显示 提交 + 详情
→ 运营提交材料
→ 需复核任务进入总管复核；无需复核任务进入等待自动复盘
→ task_report_service 从同一生命周期投影生成中文详情报告
→ task_state_machine_service 镜像任务、事件、日志到 SQLite
```

## V12.9.1 硬规则

```text
运营权限内且无需复核的任务，生成后自动接收。
自动接收后 status = 处理中。
自动接收后 lifecycleStage = accepted。
自动接收后任务卡主按钮应为“提交”。
人工接收接口必须幂等，已处理中或后续阶段不得重复写接收日志。
状态机必须能从 TaskRepository 读取并回灌任务。
详情报告必须传入请求上下文，读取同一个 task_id 的 Repository-aware 生命周期投影。
复核只属于管理任务视角。
复盘由系统自动生成周期，不作为运营按钮。
```

## 当前主 API

```text
/                                      web_demo 前端入口
/api/health                            健康检查
/api/modules/todo                      带生命周期和单动作的任务队列来源
/api/modules/todo/lifecycle/summary    任务生命周期统计
/api/modules/todo/{id}/accept          幂等接收：已处理则返回当前投影
/api/modules/todo/{id}/submit          提交材料：进入待复核或等待自动复盘
/api/modules/todo/{id}/review          复核：通过后生成自动复盘周期，退回后补充材料
/api/modules/todo/{id}/recap/complete  完成复盘并生成RAG候选
/api/modules/task-reports/tasks/{id}   Repository-aware 生命周期详情报告
/api/system/runtime-diagnostics        运行态诊断
/api/system/reset-runtime-data          清空演示运行态
```

## 部署入口

```bash
bash scripts/deploy_fast.sh
```
