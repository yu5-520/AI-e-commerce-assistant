# AI ERP 企业级电商经营 SaaS 底座

当前基线：**V16.3 本轮真实任务池验收版**。

V16.3 保留 V16.2 的真实商品判断 Agent、真实 RAG 任务映射 Agent、本轮 dataVersion 隔离、去 DEMO 垫底污染和 70% 商品判断包阀门；同时新增“本轮真实任务池验收闸门”。它不再继续生成任务，而是检查：数据页任务数、当前 dataVersion 任务池数量、任务页可见数量、详情页数量是否完全对齐。对不上就暴露断点，不自动补假任务。

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
→ 真实商品判断 Agent：按商品批次调用 LLM，输出严格 JSON judgments
→ 系统商品判断包：按真实 productId 合并判断，计算 packageConfidence
→ 70% 置信阀门：packageConfidence >= 0.70 才能进入任务映射
→ 真实任务映射 Agent：结合 RAG 权限、SOP、审批、证据、复盘规则输出严格 JSON tasks
→ 系统任务池准入：同商品同轮去重，单轮任务数受控
→ frontend_read_model_service 只按 latestRun.dataVersion 重建本轮任务读模型
→ task_pool_acceptance_v163_service 验收本轮任务池
→ /api/view/data-line 输出地铁线路状态和验收结果
→ /api/view/task-pool-acceptance 输出本轮任务池验收明细
→ /api/view/tasks 只读取本轮 dataVersion 任务
```

## V16.3 硬规则

```text
报表 Agent 只做 schema mapping，不清洗行、不判断商品、不生成任务。
商品判断 Agent 和任务映射 Agent 必须是真实批量 Agent JSON 输出。
任务池验收不生成、不修复、不补齐任务，只读数据库并暴露断点。
data-line formalTaskCount 必须等于 latestRun.taskPoolCreatedCount。
latestRun.taskPoolCreatedCount 必须等于 task_pool_entries 当前 dataVersion 数量。
task_pool_entries 当前 dataVersion 数量必须等于 frontend_task_view 当前 dataVersion 数量。
frontend_task_view 当前 dataVersion 数量必须等于 frontend_task_detail_view 当前 dataVersion 数量。
frontend_task_view 不允许保留旧 dataVersion 任务。
历史 task_pool_entries 可以留存，但不得进入当前任务页。
验收不通过时 /api/view/data-line 进入 attention。
任何不一致都不能通过刷新、mock、seed、fallback 或模板任务遮住。
```

## 验收 API

```text
/api/view/data-line                    数据页地铁线路状态，包含 taskPoolAcceptance
/api/view/task-pool-acceptance         本轮真实任务池验收明细
/api/view/tasks                        前端任务读模型，默认当前 dataVersion
/api/view/tasks/{task_id}              前端任务详情读模型，默认当前 dataVersion
```

验收通过条件：

```text
latestRun.taskPoolCreatedCount
= task_pool_entries WHERE data_version = latestRun.dataVersion
= frontend_task_view WHERE data_version = latestRun.dataVersion
= frontend_task_detail_view WHERE data_version = latestRun.dataVersion
```

## 真实 Agent 配置

```bash
# 商品判断，可与任务映射共用 DEEPSEEK_API_KEY
export PRODUCT_JUDGMENT_AGENT_API_KEY="你的模型API Key"
export PRODUCT_JUDGMENT_AGENT_MODEL="deepseek-v4-flash"
export PRODUCT_JUDGMENT_AGENT_BASE_URL="https://api.deepseek.com/chat/completions"
export PRODUCT_JUDGMENT_AGENT_BATCH_SIZE="30"
export PRODUCT_JUDGMENT_AGENT_MAX_CALLS="3"

# 任务映射，可单独配置；没有时回退读取 DEEPSEEK_API_KEY，但不会回退模板任务
export TASK_MAPPING_AGENT_API_KEY="你的模型API Key"
export TASK_MAPPING_AGENT_MODEL="deepseek-v4-flash"
export TASK_MAPPING_AGENT_BASE_URL="https://api.deepseek.com/chat/completions"
export TASK_MAPPING_AGENT_BATCH_SIZE="8"
export TASK_MAPPING_AGENT_MAX_CALLS="2"
```

## 运行态表

```text
task_generation_runs_v14              任务生成运行快照，包含 V16.2/V16.3 真实 Agent 与验收摘要来源
agent_product_judgments_v15           真实商品判断 Agent 输出后的指标级判断
product_judgment_packages_v15         系统商品判断包，包含 packageConfidence
task_generation_decisions_v15         真实任务映射 Agent 输出后的任务决策
task_pool_entries                     当前和历史任务池条目
frontend_task_view                    本轮任务读模型，按 dataVersion 隔离
frontend_task_detail_view             本轮任务详情读模型，按 dataVersion 隔离
agent_budget_ledgers_v15              全链路 Agent 预算账本
agent_call_events_v15                 Agent/API/RAG 调用事件
```

## 部署入口

```bash
bash scripts/deploy_fast.sh
```
