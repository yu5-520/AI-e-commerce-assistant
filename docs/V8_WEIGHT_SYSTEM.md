# V8.6 权重数据波动任务系统

V6-V7 是增长数据趋势任务系统，核心是发现增长机会、生成经营任务，并通过 SaaS 控制面完成权限、审批、执行、复盘和发布治理。V8 是权重数据波动任务系统，核心不再只是哪里增长，而是资源权重是否应该重新分配。

## 1. V8 总定位

```text
V8：权重数据波动任务系统
```

完整定义：

```text
基于商品、店铺、运营三类对象的多周期指标波动，结合环比、同比、多周期均值、波动率、RAG 标准线、联动比对、上下文权重修正和交叉验证，生成升权、降权、限权、修复、止损、复核等交叉任务组。
```

## 2. V8.6 本次边界

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

V8.5 已完成：

```text
对象权重评分 + 店铺角色 + 店铺权重 + 商品拖累 + 运营责任 → 上下文权重修正与任务强度提示
```

V8.6 新增：

```text
上下文修正 + 商品 / 店铺 / 运营交叉证据 + 标准线 / 联动 / 评分证据 → 交叉验证与任务组准备度
```

V8.6 仍然不做以下动作：

```text
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

## 4. V8.0 - V8.6 数据表

```text
weight_metric_snapshots_v8
weight_metric_comparisons_v8
weight_rag_standard_hits_v8
linked_metric_relations_v8
weight_scores_v8
context_weight_adjustments_v8
weight_cross_validations_v8
```

`weight_cross_validations_v8` 记录：

```text
validation_id
tenant_id
org_id
object_type
object_id
parent_type
parent_id
validation_status
validation_label
readiness
confidence
final_intensity_level
final_intensity_label
cross_score
evidence_count
conflict_count
related_adjustment_ids
related_score_ids
cross_factors
conclusion
payload
created_at
```

## 5. V8.6 交叉验证状态

```text
confirmed             交叉确认
protected_confirmed   保护型确认
conflict              存在冲突
buffered              缓冲观察
needs_review          需要复核
human_review_only     仅人工复核
insufficient_evidence 证据不足
```

准备度：

```text
ready_for_task_group  可进入任务组候选
not_ready             暂不进入任务组
human_review_only     只进入人工复核
```

注意：V8.6 只判断“准备度”，真实任务组从 V8.7 开始生成。

## 6. 商品交叉验证

商品不再只看自己的分数，而是交叉看：

```text
商品上下文修正状态
商品负向联动数量
商品 RAG 标准线异常数量
商品所在店铺权重
商品所在店铺角色
商品是否拖累高权重店铺
```

典型规则：

```text
高权重店铺 + 商品强降权提示 + 商品负向证据一致 → 保护型确认
商品强动作 + 店铺本身低权重低分 → 存在冲突，不直接归因单品
商品有正向联动或标准线大体达标 → 缓冲观察
证据不足 → 等待更多周期数据
```

## 7. 店铺交叉验证

店铺不再只看自己的分数，而是交叉看：

```text
店铺上下文修正状态
店铺标准线异常
店铺联动关系
店铺下属商品异常数量
店铺下属商品强动作数量
```

典型规则：

```text
店铺资源限制候选 + 多个商品同步异常 → 交叉确认
店铺低分但商品侧未同步异常 → 存在冲突
店铺整体健康但存在拖累单品 → 任务方向应指向商品，而不是店铺降权
```

## 8. 运营交叉验证

运营对象永远不自动处罚、不自动降权、不自动改权限。

运营交叉验证只输出：

```text
人工复核依据
辅导观察依据
升权建议依据
权限调整复核依据
```

所有运营相关结论都必须由总管或老板确认。

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
```

前端入口：

```text
权重中心
```

## 10. V8 后续节奏

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
