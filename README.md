# AI ERP 企业级电商经营 SaaS 底座

当前基线：**V14.8.3 站点链路契约与地铁线路状态版**。

V14.8.3 保留前端读模型与后台计算隔离，并继续保留 V14.8.2 的成熟任务队列规则。本版重点不是继续改 Agent 判断，而是把“链路完成”和“正式任务数量”分开。Agent 判断生成 0 个正式任务时，也会写入 `task_generation_runs_v14`，数据页用地铁站点图展示“接入、建档、全量包、判断、任务、展示”的状态。

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
→ system_product_snapshot_station 生成商品分层快照
→ product_signal_snapshot_station 生成商品全量包 fullProductBundle
→ task_signal_station 将全量包进入队列
→ rag_context_station 给出波动边界
→ agent_judgment_station_v1481_service 按 V14.8.3 链路契约逐商品判断
→ 每轮判断完成后写入 task_generation_runs_v14
→ 成熟经营判断进入 V11.8 SOP task snapshot
→ 严重数据缺口进入商品数据核验 task snapshot
→ observe_only / 后台观察只进标签或日志，不进入正式 task_pool
→ task_pool_station 进入任务池，正式任务可以为 0
→ frontend_read_model_service 重建可见任务读模型，并统一 id = taskId
→ /api/view/data-line 输出产品化地铁线路状态
→ /api/view/tasks 与 /api/modules/todo 读取任务池 / 生命周期投影
```

## V14.8.3 硬规则

```text
前端页面切换只能读 /api/view/* 或产品桥接读模型。
链路完成不等于正式任务数量。
正式任务可以是 0，但任务生成运行快照不能缺席。
Agent 每轮判断完成后必须写入 task_generation_runs_v14。
observe_only / 后台观察不进入正式任务池，但必须计入链路状态。
数据页顶部不再展示“同步：总览 / 经营 / 任务 / 数据 / 日志”等工程同步串。
数据页顶部展示地铁站点图：接入 / 建档 / 全量包 / 判断 / 任务 / 展示。
任务站点为 empty 时代表已判断但无正式任务。
正式任务仍使用 V11.8 SOP 包，生命周期仍由任务状态机处理。
```

## 当前主 API

```text
/                                      web_demo 前端入口
/api/health                            健康检查
/api/view/data-line                    数据页地铁线路状态
/api/view/products                     前端商品读模型
/api/modules/product                   商品页桥接读模型
/api/view/tasks                        前端任务读模型
/api/view/tasks/{task_id}              前端任务详情读模型
/api/modules/todo                      带生命周期和单动作的任务队列来源
/api/modules/task-reports/tasks/{id}   Repository-aware 生命周期详情报告
/api/system/runtime-diagnostics        运行态诊断
/api/system/reset-runtime-data          清空演示运行态
```

## 部署入口

```bash
bash scripts/deploy_fast.sh
```
