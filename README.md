# AI ERP 企业级电商经营 SaaS 底座

当前基线：**V16.2 真实任务映射 Agent + RAG MVP 版**。

V16.2 保留 V16.1 的真实商品判断 Agent、本轮 dataVersion 隔离、去 DEMO 垫底污染和 70% 商品判断包阀门；同时把“任务映射阶段”从权限 SOP 模板切到真实 RAG 任务映射 Agent。没有真实 API Key、模型调用失败、JSON 无效或无有效任务时，系统只记录失败，不回退模板任务、不生成假任务。

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
→ 系统校验：校验 productId、storeId、metricCode、severity、confidence、decisionHint、finding、evidence
→ 系统商品判断包：按真实 productId 合并判断，计算 packageConfidence
→ 70% 置信阀门：packageConfidence >= 0.70 才能进入任务映射
→ 真实任务映射 Agent：结合 RAG 权限、SOP、审批、证据、复盘规则输出严格 JSON tasks
→ 系统校验：校验 packageId、productId、storeId、decision、SOP、证据要求、权限边界
→ 系统任务池准入：同商品同轮去重，单轮任务数受控
→ frontend_read_model_service 只按 latestRun.dataVersion 重建本轮任务读模型
→ /api/view/data-line 输出本轮地铁线路状态、真实商品 Agent 和真实任务 Agent 调用状态
→ /api/view/tasks 只读取本轮 dataVersion 任务
```

## V16.2 硬规则

```text
报表 Agent 只做 schema mapping，不清洗行、不判断商品、不生成任务。
商品判断 Agent 必须以 fullProductBundle 批量输入，不允许按报表行、指标、任务逐条调用。
任务映射 Agent 只处理 packageConfidence >= 0.70 的商品判断包。
任务映射 Agent 必须结合 RAG 中的公司权限、账号权限、审批规则、SOP、证据要求和复盘规则。
真实任务映射 Agent 只输出 JSON tasks，不重新判断商品风险。
模型返回必须是严格 JSON，顶层必须包含 tasks 数组。
每条正式 task 必须绑定当前输入中的 packageId / productId / storeId。
每条正式 task 至少包含 3 个 sopSteps 和 2 个 evidenceRequirements。
每条正式 task 必须包含 forbiddenActions 或权限边界说明。
系统按 task_generation_decisions_v15 写入真实任务映射决策。
/api/view/tasks 默认只读 latestRun.dataVersion。
旧 DEMO / seed / fallback / history 任务不能进入当前执行队列。
API Key 缺失、provider 调用失败、JSON 无效、无有效任务时，不回退模板任务、不生成假任务。
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

## 当前主 API

```text
/                                      web_demo 前端入口
/api/health                            健康检查
/api/view/data-line                    数据页地铁线路状态
/api/view/products                     前端商品读模型，默认当前 dataVersion
/api/modules/product                   商品页桥接读模型
/api/view/tasks                        前端任务读模型，默认当前 dataVersion
/api/view/tasks/{task_id}              前端任务详情读模型，默认当前 dataVersion
/api/modules/todo                      带生命周期和单动作的任务队列来源
/api/modules/task-reports/tasks/{id}   Repository-aware 生命周期详情报告
/api/system/runtime-diagnostics        运行态诊断
/api/system/db-status                  数据库与运行态残留诊断
/api/system/reset-runtime-data          清空演示运行态
```

## 运行态表

```text
task_generation_runs_v14              任务生成运行快照，包含 V16.2 真实商品/任务 Agent 调用摘要
agent_product_judgments_v15           真实商品判断 Agent 输出后的指标级判断
product_judgment_packages_v15         系统商品判断包，包含 packageConfidence
task_generation_decisions_v15         真实任务映射 Agent 输出后的任务决策
agent_budget_ledgers_v15              全链路 Agent 预算账本
agent_call_events_v15                 Agent/API/RAG 调用事件
report_schema_mapping_cache_v15       报表 schema 指纹与字段映射缓存
frontend_task_view                    本轮任务读模型，按 dataVersion 隔离
```

## 部署入口

```bash
bash scripts/deploy_fast.sh
```
