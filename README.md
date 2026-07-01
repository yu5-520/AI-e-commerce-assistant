# AI ERP 企业级电商经营 SaaS 底座

当前基线：**V14.9.3 Agent1 指标级展开 + 商品判断包压缩版**。

V14.9.3 保留双 Agent 站点拆分和真实商品判断包硬闸，并修正 Agent1 输入颗粒度：Agent1 不再对一个商品全量包只输出一条判断，而是把一个真实商品包展开成多条指标级判断；系统整合站再按真实 `productId` 压缩回一个 `product_judgment_package`。Agent2 只消费商品判断包，任务数仍按本轮 `taskPoolCreatedCount` 显示。

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
→ Agent1 指标级分析判断站：一个商品包展开为多条 agent_product_judgments_v15
→ 系统真实商品判断包硬闸：按真实 productId 压缩写入 product_judgment_packages_v15
→ Agent2 任务生成站：只消费真实商品判断包，写入 task_generation_decisions_v15
→ 系统任务池准入站：同商品同轮去重，单轮任务数受控
→ frontend_read_model_service 重建可见任务读模型，并统一 id = taskId
→ /api/view/data-line 输出本轮地铁线路状态
→ /api/view/tasks 与 /api/modules/todo 读取任务池 / 生命周期投影
```

## V14.9.3 硬规则

```text
Agent1 不允许生成任务、SOP 或入池动作。
Agent1 必须把真实商品全量包展开成多条指标级判断。
系统整合站必须绑定真实 productId。
缺少真实 productId 的判断只记录身份缺口，不进入 Agent2。
禁止使用 entityId / bundleId / signalId / SKU / SPU / LINK 作为商品判断包 ID。
同一真实商品的多条指标判断必须压缩成一个 product_judgment_package。
Agent2 只接收真实 product_judgment_package。
Agent2 任务生成有单轮上限。
任务池准入前检查同 dataVersion + storeId + productId 是否已有任务。
数据页“正式任务”显示本轮 taskPoolCreatedCount，不显示全局 task_pool_entries 总数。
判断数量应该大于或等于判断包数量；任务数量必须受控。
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

## 运行态表

```text
task_generation_runs_v14          任务生成运行快照
agent_product_judgments_v15       Agent1 指标级原始判断
product_judgment_packages_v15     系统商品判断包
task_generation_decisions_v15     Agent2 任务生成决策
```

## 部署入口

```bash
bash scripts/deploy_fast.sh
```
