# AI ERP 企业级电商经营 SaaS 底座

当前基线：**V15 全链路 Agent 预算账本 + Agent 网关版**。

V15 把 Agent 从“到处调用 API 的功能点”升级为“有职责、有预算、有缓存、有降级、有权限边界的站点能力”。系统正式拆成三类 Agent：报表 Agent 只做 schema mapping，商品判断 Agent 只做商品全量包判断和置信值，任务映射 Agent 只做公司权限、账号权限、审批规则、SOP RAG 的任务映射。所有 Agent/API/RAG 调用必须登记到 `agent_budget_ledgers_v15` 和 `agent_call_events_v15`。

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
→ 报表 Agent：只识别文件名、sheet、表头、样例值，输出 report_schema_mapping
→ 系统代码清洗：按 schema mapping 清洗全部行并写入事实表
→ system_product_snapshot_station 生成商品分层快照
→ product_signal_snapshot_station 生成商品全量包 fullProductBundle
→ 商品判断 Agent：分析垂直类目、数据变化、趋势、环比/同比/连比、RAG基准和置信值
→ 系统商品判断包：按真实 productId 合并判断，计算 packageConfidence
→ 70% 置信阀门：packageConfidence >= 0.70 才能进入任务映射
→ 任务映射 Agent：检索公司权限、账号权限、审批规则、SOP RAG，生成权限约束任务
→ 系统任务池准入：同商品同轮去重，单轮任务数受控
→ frontend_read_model_service 重建可见任务读模型，并统一 id = taskId
→ /api/view/data-line 输出本轮地铁线路状态和全链路 Agent 预算状态
→ /api/view/tasks 与 /api/modules/todo 读取任务池 / 生命周期投影
```

## V15 硬规则

```text
报表 Agent 只做 schema mapping，不清洗行、不判断商品、不生成任务。
报表 schema 识别必须支持 schema_fingerprint 和 report_schema_mapping_cache。
商品判断 Agent 只做商品全量包判断、趋势判断、类目/权重/RAG基准判断和置信值。
商品判断 Agent 不生成任务、不写 SOP、不决定任务池。
系统按真实 productId 合并同商品判断，并计算 packageConfidence。
packageConfidence < 0.70 只能进入观察池，不能进入任务映射 Agent。
任务映射 Agent 只处理 70%+ 商品判断包。
任务映射 Agent 必须检索公司权限、账号权限、审批规则和 SOP RAG。
任务映射输出必须包含执行角色、审批角色、禁止动作、时限、证据要求和复盘指标。
所有 Agent 调用必须通过 V15 Agent Budget Ledger / Gateway。
API 调用不能按报表行、指标判断、商品判断包或任务条数线性增长。
默认单轮预算：报表 Agent 0-3 次，商品判断 Agent 0-3 次，任务映射 Agent 0-2 次，总 Agent 调用 <= 8 次。
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
task_generation_runs_v14              任务生成运行快照，包含 V15 Agent 预算摘要
agent_product_judgments_v15           商品判断 Agent 指标级原始判断
product_judgment_packages_v15         系统商品判断包，包含 packageConfidence
task_generation_decisions_v15         任务映射决策
agent_budget_ledgers_v15              全链路 Agent 预算账本
agent_call_events_v15                 Agent/API/RAG 调用事件
report_schema_mapping_cache_v15       报表 schema 指纹与字段映射缓存
```

## 部署入口

```bash
bash scripts/deploy_fast.sh
```
