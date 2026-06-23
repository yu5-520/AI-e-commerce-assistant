# V8.9 权重数据波动任务系统

V6-V7 是增长数据趋势任务系统，核心是发现增长机会、生成经营任务，并通过 SaaS 控制面完成权限、审批、执行、复盘和发布治理。V8 是权重数据波动任务系统，核心不再只是哪里增长，而是资源权重是否应该重新分配。

## 1. V8 总定位

```text
V8：权重数据波动任务系统
```

完整定义：

```text
基于商品、店铺、运营三类对象的多周期指标波动，结合环比、同比、多周期均值、波动率、RAG 标准线、联动比对、上下文权重修正、交叉验证、审批门控、执行回写和复盘沉淀，生成并治理升权、降权、限权、修复、止损、复核等交叉任务组。
```

## 2. V8.9 本次边界

V8.0 已完成：商品 / 店铺 / 运营权重指标快照。  
V8.1 已完成：环比 / 同比 / 多周期均值 / 波动率。  
V8.2 已完成：RAG 标准线命中。  
V8.3 已完成：多指标联动比对。  
V8.4 已完成：对象权重评分。  
V8.5 已完成：上下文权重修正和任务强度提示。  
V8.6 已完成：交叉验证和任务组准备度。  
V8.7 已完成：交叉任务组草案生成。  
V8.8 已完成：权重审批流和执行门控。

V8.9 新增：

```text
审批通过 → 执行回写记录 → 人工提交执行结果 → 调整后复盘 → RAG 案例候选
```

V8.9 仍然不做以下动作：

```text
不直接调用平台 API 执行
不自动下架商品
不自动调整投产
不自动处罚运营
不自动改变人员权限
不自动改写 RAG 标准线
```

## 3. V8 主链路

```text
经营数据 / 组织数据进入
↓
商品 / 店铺 / 运营权重指标快照
↓
环比 / 同比 / 多周期均值 / 波动率
↓
RAG 标准线命中
↓
多指标联动比对
↓
对象权重评分
↓
上下文权重修正
↓
交叉验证
↓
交叉任务组生成
↓
审批流
↓
执行回写
↓
调整后复盘
↓
权重规则沉淀
↓
资源调度看板
```

## 4. V8.0 - V8.9 数据表

```text
weight_metric_snapshots_v8
weight_metric_comparisons_v8
weight_rag_standard_hits_v8
linked_metric_relations_v8
weight_scores_v8
context_weight_adjustments_v8
weight_cross_validations_v8
weight_task_groups_v8
weight_approval_flows_v8
weight_execution_feedback_v8
weight_execution_reviews_v8
```

`weight_execution_feedback_v8` 记录：

```text
execution_id
approval_id
task_group_id
object_type
object_id
group_type
group_name
execution_status
execution_gate
planned_actions
actual_actions
before_state
after_state
result_metrics
evidence_refs
executor_id
feedback_note
completed_at
```

`weight_execution_reviews_v8` 记录：

```text
review_id
execution_id
approval_id
task_group_id
object_type
object_id
review_status
effectiveness
next_decision
review_summary
review_factors
rag_memory_candidate
```

## 5. V8.9 执行回写状态

```text
awaiting_feedback    等待人工回写执行结果
feedback_submitted   执行结果已回写
```

执行门：

```text
feedback_required    审批通过后等待回写
review_pending       回写完成，等待复盘
```

## 6. V8.9 调整后复盘

复盘效果：

```text
effective    执行后改善
worse        执行后恶化
uncertain    暂不确定，继续观察
```

下一决策：

```text
keep_or_restore          保留 / 恢复当前策略
escalate_review          升级复核
continue_observation     继续观察一个周期
```

RAG 规则：

```text
复盘案例可以成为 RAG 记忆候选；
但不能自动改写公司标准线、权重规则或审批规则。
```

## 7. 当前接口

```text
GET  /api/architecture/v8/weight-snapshots
POST /api/architecture/v8/weight-snapshots/generate
GET  /api/architecture/v8/weight-comparisons
POST /api/architecture/v8/weight-comparisons/generate
GET  /api/architecture/v8/weight-rag-hits
POST /api/architecture/v8/weight-rag-hits/generate
GET  /api/architecture/v8/linked-relations
POST /api/architecture/v8/linked-relations/generate
GET  /api/architecture/v8/weight-scores
POST /api/architecture/v8/weight-scores/generate
GET  /api/architecture/v8/context-weights
POST /api/architecture/v8/context-weights/generate
GET  /api/architecture/v8/cross-validations
POST /api/architecture/v8/cross-validations/generate
GET  /api/architecture/v8/weight-task-groups
POST /api/architecture/v8/weight-task-groups/generate
GET  /api/architecture/v8/weight-approvals
POST /api/architecture/v8/weight-approvals/generate
POST /api/architecture/v8/weight-approvals/{approval_id}/decide
GET  /api/architecture/v8/weight-executions
POST /api/architecture/v8/weight-executions/generate
POST /api/architecture/v8/weight-executions/{execution_id}/feedback
GET  /api/architecture/v8/weight-execution-reviews
POST /api/architecture/v8/weight-execution-reviews/generate
```

前端入口：

```text
权重中心
```

## 8. V8 后续节奏

```text
V8.0 权重指标快照层
V8.1 周期比较计算层
V8.2 RAG 标准线命中层
V8.3 联动比对层
V8.4 对象权重评分层
V8.5 上下文权重修正层
V8.6 交叉验证层
V8.7 交叉任务组生成层
V8.8 权重审批流
V8.9 执行回写与调整后复盘
V8.10 权重资源调度看板
```

## 9. V8 核心边界

```text
系统可以建议升权 / 降权；
系统可以生成复核任务；
系统可以给出数据证据；
系统可以走审批链；
系统可以记录执行结果并生成复盘；
系统不能自动处罚运营；
系统不能自动剥夺权限；
系统不能自动改变组织关系；
系统不能自动改写 RAG 标准线；
系统不能绕过总管 / 老板确认。
```
