# V8.5 权重数据波动任务系统

V6-V7 是增长数据趋势任务系统，核心是发现增长机会、生成经营任务，并通过 SaaS 控制面完成权限、审批、执行、复盘和发布治理。V8 是权重数据波动任务系统，核心不再只是哪里增长，而是资源权重是否应该重新分配。

## 1. V8 总定位

```text
V8：权重数据波动任务系统
```

完整定义：

```text
基于商品、店铺、运营三类对象的多周期指标波动，结合环比、同比、多周期均值、波动率、RAG 标准线、联动比对和上下文权重修正，进行交叉验证，并生成升权、降权、限权、修复、止损、复核等交叉任务组。
```

## 2. V8.5 本次边界

V8.0 已完成：

```text
商品 / 店铺 / 运营 → 权重指标快照
```

V8.1 已完成：

```text
权重指标快照 → 环比 / 多周期均值 / 波动率 / 可用同比
```

V8.2 已完成：

```text
权重指标快照 + 周期比较 → RAG 标准线命中
```

V8.3 已完成：

```text
周期比较 + RAG 标准线 + 多指标组合 → 联动比对解释
```

V8.4 已完成：

```text
联动关系 + 标准线命中 + 周期比较 → 对象权重评分与状态
```

V8.5 新增：

```text
对象权重评分 + 店铺角色 + 店铺权重 + 商品拖累 + 运营责任 → 上下文权重修正与任务强度提示
```

V8.5 仍然不做以下动作：

```text
不做交叉验证
不真正生成权重任务
不执行升降权
不自动下架商品
不自动调整投产
不自动处罚运营
不自动改变人员权限
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
任务强度判断
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

## 4. V8.0 - V8.5 数据表

```text
weight_metric_snapshots_v8
weight_metric_comparisons_v8
weight_rag_standard_hits_v8
linked_metric_relations_v8
weight_scores_v8
context_weight_adjustments_v8
```

`context_weight_adjustments_v8` 记录：

```text
adjustment_id
tenant_id
org_id
object_type
object_id
parent_type
parent_id
base_score
adjusted_score
base_state
adjusted_state
adjusted_label
risk_level
task_intensity_level
task_intensity_label
context_type
context_summary
context_factors
related_score_id
payload
created_at
```

## 5. V8.5 上下文修正规则

商品上下文：

```text
高权重保护型店铺 + 商品低分 → 放大处理强度
品牌主店 / 利润核心店 / 流量核心店 → 保护店铺资产优先
测试店 / 低权重店 + 商品低分 → 增加试错缓冲
成长店 + 短期波动 → 谨慎修正，避免打断增长
商品流量占比高 + 低分 + 高权重店铺 → 提示拖累店铺资产风险
```

店铺上下文：

```text
保护型店铺高分 → 高权重经营资产
保护型店铺低分 → 更快总管介入
测试型店铺低分 → 允许更长测试周期
```

运营上下文：

```text
运营权重只用于复核和建议
多店铺责任下的低分需要结合店铺难度复核
高分运营可形成升权建议证据
任何运营相关修正都不能自动处罚或自动改权限
```

## 6. V8.5 任务强度提示

商品 / 店铺强度：

```text
L1 观察
L2 修复
L3 降权候选
L4 强降权候选
L5 止损复核
```

运营强度：

```text
H1 人工复核依据
H2 辅导观察
H3 权限调整复核
```

注意：V8.5 只输出“任务强度提示”，不生成真实任务。真实任务组从 V8.7 开始。

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
```

前端入口：

```text
权重中心
```

## 8. V8 后续节奏

```text
V8.0 权重指标快照层
V8.1 周期比较计算层：环比、同比、多周期均值、波动率
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
