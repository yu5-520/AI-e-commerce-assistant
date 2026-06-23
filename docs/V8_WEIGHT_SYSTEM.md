# V8.8 权重数据波动任务系统

V6-V7 是增长数据趋势任务系统，核心是发现增长机会、生成经营任务，并通过 SaaS 控制面完成权限、审批、执行、复盘和发布治理。V8 是权重数据波动任务系统，核心不再只是哪里增长，而是资源权重是否应该重新分配。

## 1. V8 总定位

```text
V8：权重数据波动任务系统
```

完整定义：

```text
基于商品、店铺、运营三类对象的多周期指标波动，结合环比、同比、多周期均值、波动率、RAG 标准线、联动比对、上下文权重修正、交叉验证和审批门控，生成并治理升权、降权、限权、修复、止损、复核等交叉任务组。
```

## 2. V8.8 本次边界

V8.0 已完成：商品 / 店铺 / 运营权重指标快照。  
V8.1 已完成：环比 / 同比 / 多周期均值 / 波动率。  
V8.2 已完成：RAG 标准线命中。  
V8.3 已完成：多指标联动比对。  
V8.4 已完成：对象权重评分。  
V8.5 已完成：上下文权重修正和任务强度提示。  
V8.6 已完成：交叉验证和任务组准备度。  
V8.7 已完成：交叉任务组草案生成。

V8.8 新增：

```text
权重任务组草案 → 审批流 → 通过 / 拒绝 / 退回复核 → 执行门控
```

V8.8 仍然不做以下动作：

```text
不自动执行升降权
不自动下架商品
不自动调整投产
不自动处罚运营
不自动改变人员权限
不绕过总管 / 老板确认
```

审批通过只把任务组推到“待执行层”；V8.9 才处理执行回写和复盘。

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

## 4. V8.0 - V8.8 数据表

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
```

`weight_approval_flows_v8` 记录：

```text
approval_id
task_group_id
object_type
object_id
group_type
group_name
approval_status
approval_role
approval_required
execution_gate
priority
final_intensity_level
requested_by
decided_by
decision_note
approval_steps
evidence_refs
payload
created_at
updated_at
decided_at
```

## 5. V8.8 审批状态

```text
pending               待审批
evidence_review       证据复核
human_review          人工复核
approved              已通过
reviewed              人工已复核
rejected              已拒绝
returned_for_evidence 退回复核
```

执行门：

```text
locked                审批前锁定
ready_for_execution   审批通过，等待 V8.9 执行层
blocked               拒绝或退回复核
human_review_only     只允许人工复核，不进入自动执行
```

## 6. 审批权限

```text
manager 可审批 manager 级任务组
owner 可审批 owner / manager 级任务组
operator / finance 不可审批权重任务组
```

商品和店铺的高风险任务组需要 owner 或 manager 审批；人员相关任务组只进入人工复核或老板确认，不自动执行权限变化。

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
系统不能自动处罚运营；
系统不能自动剥夺权限；
系统不能自动改变组织关系；
系统不能绕过总管 / 老板确认。
```
