# V8.7 权重数据波动任务系统

V6-V7 是增长数据趋势任务系统，核心是发现增长机会、生成经营任务，并通过 SaaS 控制面完成权限、审批、执行、复盘和发布治理。V8 是权重数据波动任务系统，核心不再只是哪里增长，而是资源权重是否应该重新分配。

## 1. V8 总定位

```text
V8：权重数据波动任务系统
```

完整定义：

```text
基于商品、店铺、运营三类对象的多周期指标波动，结合环比、同比、多周期均值、波动率、RAG 标准线、联动比对、上下文权重修正和交叉验证，生成升权、降权、限权、修复、止损、复核等交叉任务组。
```

## 2. V8.7 本次边界

V8.0 已完成：商品 / 店铺 / 运营权重指标快照。  
V8.1 已完成：环比 / 同比 / 多周期均值 / 波动率。  
V8.2 已完成：RAG 标准线命中。  
V8.3 已完成：多指标联动比对。  
V8.4 已完成：对象权重评分。  
V8.5 已完成：上下文权重修正和任务强度提示。  
V8.6 已完成：交叉验证和任务组准备度。

V8.7 新增：

```text
交叉验证结果 → 权重任务组草案 → 待审批 / 证据复核 / 人工复核
```

V8.7 仍然不做以下动作：

```text
不绕过审批
不自动执行升降权
不自动下架商品
不自动调整投产
不自动处罚运营
不自动改变人员权限
```

任务组在 V8.7 只是结构化草案；V8.8 才接审批流。

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

## 4. V8.0 - V8.7 数据表

```text
weight_metric_snapshots_v8
weight_metric_comparisons_v8
weight_rag_standard_hits_v8
linked_metric_relations_v8
weight_scores_v8
context_weight_adjustments_v8
weight_cross_validations_v8
weight_task_groups_v8
```

`weight_task_groups_v8` 记录：

```text
task_group_id
tenant_id
org_id
object_type
object_id
parent_type
parent_id
group_type
group_name
group_status
priority
approval_required
approval_role
final_intensity_level
readiness
validation_status
task_count
tasks
evidence_refs
related_validation_id
payload
created_at
```

## 5. V8.7 任务组状态

```text
pending_approval      待审批任务组
evidence_review       证据复核任务组
human_review_draft    人工复核草案
```

任务组优先级：

```text
P0 重大止损 / 权限调整复核
P1 强降权 / 店铺资源限制 / 辅导观察
P2 冲突复核 / 证据补充
P3 常规观察 / 修复
```

## 6. 商品任务组

商品任务组会根据最终强度生成不同草案：

```text
L5 商品止损复核任务组：停止扩大投产、首页主打位替换、下架/清仓复核
L4 商品强降权任务组：快速降低投产、主推位置调整、承接修复复核
L3 商品降权候选任务组：降低测试预算、商品承接修复
L1-L2 商品修复观察任务组：标题主图测试、复盘观察
```

高权重店铺中的拖累商品，会生成更强的任务组草案；低权重/测试店铺中的商品，会优先生成修复或复核任务组。

## 7. 店铺任务组

```text
店铺资源限制复核任务组：限制上新/投放额度、总管介入、老板审批
店铺观察修复任务组：店铺结构复核、异常商品定位
```

V8.7 的店铺任务组仍是草案，涉及店铺资源收缩、预算收缩、扩权或降权时，必须进入 V8.8 审批。

## 8. 运营任务组

运营对象永远不自动处罚、不自动降权、不自动改权限。

```text
运营权限调整复核任务组：权限调整复核、老板确认
运营辅导观察任务组：辅导观察、周期复盘
运营人工复核任务组：人工复核材料整理
```

所有运营相关任务组都必须由总管或老板确认。

## 9. 当前接口

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
```

前端入口：

```text
权重中心
```

## 10. V8 后续节奏

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

## 11. V8 核心边界

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
