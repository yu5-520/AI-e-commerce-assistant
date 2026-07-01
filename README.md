# AI ERP 企业级电商经营 SaaS 底座

当前基线：**V14.9.1 双 Agent 运行态清空边界修复版**。

V14.9.1 保留 V14.9 的双 Agent 站点拆分：Agent1 只做商品/指标分析判断，系统按商品压缩为 `product_judgment_package`，Agent2 再基于商品判断包生成商品级 SOP 任务。本版只修清空运行态边界：清空演示数据时必须同时清掉任务生成运行快照和 V15 双 Agent 表，避免出现“接入 0、全量包 0，但判断仍有残留”的假链路状态。

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
→ Agent1 商品分析判断站：写入 agent_product_judgments_v15
→ 系统商品判断包整合站：写入 product_judgment_packages_v15
→ Agent2 任务生成站：写入 task_generation_decisions_v15
→ 系统任务池准入站：只放入商品级 SOP 任务
→ task_pool_station 进入任务池，正式任务可以为 0
→ frontend_read_model_service 重建可见任务读模型，并统一 id = taskId
→ /api/view/data-line 输出产品化地铁线路状态
→ /api/view/tasks 与 /api/modules/todo 读取任务池 / 生命周期投影
```

## V14.9.1 硬规则

```text
Agent1 不允许生成任务、SOP 或入池动作。
Agent1 只输出指标级/商品级分析判断。
系统必须按 dataVersion + storeId + productId 整合 product_judgment_package。
Agent2 只接收 product_judgment_package。
Agent2 才允许生成任务标题、优先级、SOP、证据要求。
任务池只接收系统准入后的商品级任务。
同一商品同一轮默认最多 1 个正式经营任务。
判断数量可以多，任务数量必须受控。
数据页顶部展示地铁站点图：接入 / 建档 / 全量包 / 判断 / 整合 / 任务 / 展示。
清空运行态必须清除 task_generation_runs_v14 和 V15 双 Agent 表。
事实源为 0 时，V14/V15 链路产物必须也为 0。
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
/api/system/db-status                  数据库与运行态残留诊断
/api/system/reset-runtime-data          清空演示运行态
```

## 运行态清空范围

```text
task_generation_runs_v14          任务生成运行快照
agent_product_judgments_v15       Agent1 原始分析判断
product_judgment_packages_v15     系统商品判断包
task_generation_decisions_v15     Agent2 任务生成决策
```

## 部署入口

```bash
bash scripts/deploy_fast.sh
```
