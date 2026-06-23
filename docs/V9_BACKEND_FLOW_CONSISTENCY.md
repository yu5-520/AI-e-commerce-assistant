# V9.2 后端主流程一致性

V9.2 是后端主流程一致性版本。

V9.0 统一 SaaS 企业级一致性底座，V9.1 统一仓库结构，V9.2 开始固定后端主流程：把 V8 权重能力从旁路架构接口收束为后端增强层，并明确报表导入、模块投影、权重信号、任务、Agent、审批、执行回写、复盘和 RAG 候选之间的契约。

## 1. V9.2 目标

```text
不新增前端主模块。
不继续扩展 V8 新算法。
不自动执行平台经营动作。
固定后端主流程契约。
让 CI 能检查主流程入口没有断。
```

## 2. 后端主流程

```text
ImportJob
↓
DataVersion
↓
RawRows
↓
ModuleProjection
↓
AlertEvent
↓
WeightSignal
↓
DecisionTask
↓
AgentReport
↓
ApprovalFlow
↓
ExecutionFeedback
↓
ReviewLog
↓
RagMemoryCandidate
```

这条链路不是要求一次性把所有自动化全部做完，而是先把后端契约定死：

```text
导入之后，哪些服务负责数据版本？
哪些服务负责模块投影？
哪些服务负责预警和趋势？
V8 权重能力从哪里进入？
Agent 生成任务时读取哪些证据？
审批流在哪里拦截？
执行回写在哪里记录？
复盘和 RAG 候选在哪里沉淀？
```

## 3. 主流程阶段与责任

### 3.1 ImportJob

入口：

```text
/api/data/preview
/api/data/import/confirm
/api/data/import/report
```

责任：

```text
报表预览
字段映射
确认导入
创建数据版本
触发后续预警、趋势和任务候选
```

主要文件：

```text
src/api/routes/data_import.py
src/services/report_schema_service.py
src/services/report_alert_service.py
```

### 3.2 DataVersion / RawRows

入口：

```text
/api/data/versions
/api/data/import-records
/api/data/versions/{data_version}/detail
```

责任：

```text
保存导入批次
保存原始行和字段映射
支持版本详情、回滚、Demo 删除
为任务、预警、复盘提供追溯源
```

主要文件：

```text
src/services/data_version_service.py
src/services/report_alert_service.py
```

### 3.3 ModuleProjection

入口：

```text
/api/modules/dashboard
/api/modules/operating-unit
/api/modules/product
/api/modules/report
```

责任：

```text
把导入结果投影到总览、经营单元、商品、报表和任务视图
保持前端模块稳定
V8 权重结果后续以增强字段进入原模块
```

主要文件：

```text
src/api/routes/modules/
src/services/module_projection_service.py
src/services/dashboard_service.py
```

### 3.4 AlertEvent / TrendSignal

入口：

```text
/api/data/alerts
/api/data/v3-summary
/api/modules/trend
```

责任：

```text
从导入数据生成预警
生成趋势信号
生成风险分级任务候选
```

主要文件：

```text
src/services/report_alert_service.py
src/services/trend_signal_service.py
src/services/risk_task_service.py
```

### 3.5 WeightSignal

入口：

```text
/api/architecture/v8/weight-snapshots
/api/architecture/v8/weight-comparisons
/api/architecture/v8/weight-rag-hits
/api/architecture/v8/linked-relations
/api/architecture/v8/weight-scores
/api/architecture/v8/context-weights
/api/architecture/v8/cross-validations
```

责任：

```text
商品 / 店铺 / 运营权重快照
周期比较
RAG 标准线命中
联动比对
权重评分
上下文修正
交叉验证
```

V9.2 规则：

```text
V8 权重能力是后端增强层。
店铺权重补强经营单元。
商品权重补强商品模块。
交叉验证补强任务详情和 Agent 报告。
不新增前端主模块。
```

### 3.6 DecisionTask / AgentReport

入口：

```text
/api/modules/agents
/api/modules/agents/tasks/generate
/api/modules/agents/{module}/{entity_id}
/api/modules/task-report
```

责任：

```text
Agent 根据模块数据、权重上下文、RAG 证据和 ActionPlan 生成任务方案
任务方案必须带证据链
不能按模块套同一模板
不能越过人工确认执行动作
```

主要文件：

```text
src/api/routes/modules/agents.py
src/api/routes/modules/task_report.py
src/services/task_agent_service.py
src/services/module_agent_service.py
src/services/action_plan_service.py
```

### 3.7 ApprovalFlow

入口：

```text
/api/approvals
/api/architecture/v8/weight-approvals
```

责任：

```text
高风险任务进入审批
权重动作进入审批
企业版关键后端修改进入高层审批
审批只解锁后续记录层，不直接执行平台动作
```

主要文件：

```text
src/api/routes/approvals.py
src/services/approval_lifecycle_service.py
src/services/v88_weight_approval_service.py
```

### 3.8 ExecutionFeedback

入口：

```text
/api/architecture/v8/weight-executions
/api/architecture/v8/weight-executions/{execution_id}/feedback
```

责任：

```text
记录人工实际执行动作
记录截图、链接、说明和前后指标
只做执行回写，不直接改商品、投产、权限或 RAG 标准线
```

主要文件：

```text
src/services/v89_weight_execution_review_service.py
src/services/execution_feedback_service.py
```

### 3.9 ReviewLog / RagMemoryCandidate

入口：

```text
/api/architecture/v8/weight-execution-reviews
/api/modules/rag-memory
/api/modules/feedback-flywheel
/api/modules/log
```

责任：

```text
生成调整后复盘
形成经验卡候选
进入人工复核
通过后才进入正式 RAG 记忆
```

主要文件：

```text
src/services/v89_weight_execution_review_service.py
src/api/routes/modules/rag_memory.py
src/api/routes/modules/feedback_flywheel.py
src/api/routes/modules/log.py
```

## 4. V9.2 架构可视入口

新增入口：

```text
/api/architecture/v9/backend-flow
```

主要文件：

```text
src/services/v92_backend_flow_service.py
src/api/routes/architecture.py
```

这个接口只输出后端主流程契约，不执行经营动作。

## 5. 健康检查与 Agent 版本

V9.2 要求：

```text
src/api/main.py              API_VERSION = 9.2.0
src/api/routes/health.py     API_VERSION = 9.2.0
src/api/routes/modules/agents.py  AGENT_REGISTRY_VERSION = 9.2.0
```

原因：

```text
FastAPI app.version
/api/health version
/api/modules/agents version
必须同源，避免 CI 和前端判断版本漂移。
```

## 6. CI 检查

V9.2 新增：

```text
scripts/check_backend_flow_consistency.py
```

检查内容：

```text
V9.2 文档存在
V9.2 服务存在
/api/architecture/v9/backend-flow 路由存在
导入路由包含 preview / confirm / report
模块路由包含 dashboard / operating-unit / product / task-report / agents / rag-memory / feedback-flywheel / todo / log
V8 权重路由完整
健康检查版本与 Agent registry 版本对齐
前端缓存为 9.2.0
```

## 7. Definition of Done

```text
Current Version = v9.2.0。
FastAPI API_VERSION = 9.2.0。
Health API_VERSION = 9.2.0。
Agent registry version = 9.2.0。
新增 docs/V9_BACKEND_FLOW_CONSISTENCY.md。
新增 src/services/v92_backend_flow_service.py。
新增 /api/architecture/v9/backend-flow。
新增 scripts/check_backend_flow_consistency.py。
GitHub Actions 跑 backend flow consistency check。
README、VERSION、CHANGELOG、前端缓存全部对齐 V9.2。
```
