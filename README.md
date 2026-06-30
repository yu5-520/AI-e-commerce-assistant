# AI ERP 企业级电商经营 SaaS 底座

当前基线：**V14.8.2 商品数据时间与成熟任务队列修复版**。

V14.8.2 保留 V14.8 的“前端读模型 / 后台计算隔离”设计，并继续保留 V14.8.1 的商品事实恢复能力。本版修复三个实测问题：商品指标小字出现“商品对象缓存 · 最新”等工程语言；任务生成从 0 个跳到 20 个泛化“经营任务”；任务详情页因 taskId / id 不统一导致加载失败。现在商品指标只展示业务数据时间，Agent 只有成熟经营判断或严重数据缺口才能进入正式任务池，任务读模型统一暴露 `id = taskId`。

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
→ system_product_snapshot_station 生成商品分层快照
→ product_signal_snapshot_station 生成商品全量包 fullProductBundle
→ task_signal_station 将全量包进入队列
→ rag_context_station 给出波动边界
→ agent_judgment_station_v1481_service 按 V14.8.2 mature-only 规则逐商品判断
→ 成熟经营判断生成 V11.8 SOP task snapshot
→ 严重数据缺口生成 商品数据核验 task snapshot
→ observe_only / 后台观察只进标签或日志，不进入正式 task_pool
→ task_pool_station 进入任务池
→ frontend_read_model_service 重建可见任务读模型，并统一 id = taskId
→ /api/view/tasks 与 /api/modules/todo 读取任务池 / 生命周期投影
→ task_lifecycle_state_machine_service 自动接收权限内任务
→ 前端任务卡显示 提交 + 详情
→ 运营提交材料
→ 需复核任务进入总管复核；无需复核任务进入等待自动复盘
→ task_report_service 从同一生命周期投影生成中文详情报告
→ task_state_machine_service 镜像任务、事件、日志到 SQLite
```

## V14.8.2 硬规则

```text
前端页面切换只能读 /api/view/* 或产品桥接读模型，不得触发后台计算。
商品指标事实只显示业务数据时间，如 2026.6.25，不显示缓存、读模型、投影等工程词。
报表日期优先级：报表日期字段 > 文件名 / dataVersion 日期 > 上传 / 创建日期。
Agent 的确定性路由是进入正式任务池的唯一准入线。
LLM 只能丰富文案，不能把 observe_only / 后台观察升级成正式任务。
后台观察、候选、合并、噪声不进入正式任务池。
成熟经营判断和严重数据缺口必须逐条流式入池，不等待整个 worker 批次结束。
任务列表、任务详情、任务报告必须使用同一个 taskId；前端读模型必须带 id = taskId。
正式任务仍使用 V11.8 SOP 包，生命周期仍由任务状态机处理。
```

## 当前主 API

```text
/                                      web_demo 前端入口
/api/health                            健康检查
/api/view/products                     前端商品读模型
/api/modules/product                   商品页桥接读模型：frontend_product_view + product projection
/api/view/tasks                        前端任务读模型
/api/view/tasks/{task_id}              前端任务详情读模型
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
