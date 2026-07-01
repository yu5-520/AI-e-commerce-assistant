# AI ERP 企业级电商经营 SaaS 底座

当前基线：**V16.4 真实报表事实层修复版**。

V16.4 保留 V16.2 的真实商品判断 Agent、真实 RAG 任务映射 Agent，以及 V16.3 的本轮任务池验收闸门；这次重点修复 Agent 上游的真实报表事实层。商品经营明细才建商品主档，流量来源明细只挂为子事实；商品 ROI、店铺 ROI、流量 ROI 分命名空间；指标日期优先读报表统计日期/更新时间，不再用今日时间顶替。

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
→ 真实报表事实层：商品 / 店铺 / 流量来源分命名空间
→ 商品主档去重：platform + store + productId + skuId
→ system_product_snapshot_station 生成商品分层快照，携带 productMetricFacts / trafficSourceFacts / metricDate
→ product_signal_snapshot_station 生成带 factLayerValidation 的 fullProductBundle
→ 真实商品判断 Agent：按商品批次调用 LLM，输出严格 JSON judgments
→ 系统商品判断包：按真实 productId 合并判断，计算 packageConfidence
→ 70% 置信阀门：packageConfidence >= 0.70 才能进入任务映射
→ 真实任务映射 Agent：结合 RAG 权限、SOP、审批、证据、复盘规则输出严格 JSON tasks
→ 系统任务池准入：同商品同轮去重，单轮任务数受控
→ frontend_read_model_service 只按 latestRun.dataVersion 重建本轮任务读模型
→ task_pool_acceptance_v163_service 验收本轮任务池
```

## V16.4 硬规则

```text
报表 Agent 只做 schema mapping，不清洗行、不判断商品、不生成任务。
商品经营明细 -> product master + product_metric_facts。
流量来源明细 -> trafficSourceFacts，只作为商品子事实，不创建商品主档。
店铺经营汇总 -> store_metric_facts，不覆盖商品详情页主指标。
商品详情页 ROI 只读 product_metric_facts.roi。
traffic_source_facts.roi 可显示在流量来源模块，但不得覆盖商品 ROI。
metricDate/reportDate/dataDate 优先级：统计日期 -> 更新时间 -> 文件名/dataVersion。
上传时间/current date 只能是 uploaded_at/created_at，不能是业务指标日期。
商品主键：platform + storeId/storeName + productId + skuId。
fullProductBundle 必须携带 factLayerValidation、productMetricFactCount、trafficSourceFactCount、metricDate、roiSource。
真实 Agent 只吃事实层验收后的 fullProductBundle。
```

## 验收重点

```text
建档商品数 = 商品经营明细 distinct(platform + store + productId + skuId)
全量包数 = 建档商品数
P10003 等商品 ROI 显示商品经营明细 ROI，不被流量来源 ROI=0 覆盖
指标日期显示 2026-06-25 / 2026-06-28，而不是当前日期
流量来源显示为 trafficSourceFacts 子事实
Agent 判断输入中能看到 factLayerValidation
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
system_product_snapshots_v14          商品分层快照，V16.4 携带 productMetricFacts / trafficSourceFacts / metricDate
task_generation_runs_v14              任务生成运行快照，包含真实 Agent 与验收摘要来源
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