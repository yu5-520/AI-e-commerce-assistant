# V8.2 权重数据波动任务系统

V6-V7 是增长数据趋势任务系统，核心是发现增长机会、生成经营任务，并通过 SaaS 控制面完成权限、审批、执行、复盘和发布治理。V8 是权重数据波动任务系统，核心不再只是哪里增长，而是资源权重是否应该重新分配。

## 1. V8 总定位

```text
V8：权重数据波动任务系统
```

完整定义：

```text
基于商品、店铺、运营三类对象的多周期指标波动，结合环比、同比、多周期均值、波动率、RAG 标准线、联动比对和上下文权重修正，进行交叉验证，并生成升权、降权、限权、修复、止损、复核等交叉任务组。
```

## 2. V8.2 本次边界

V8.0 已完成：

```text
商品 / 店铺 / 运营 → 权重指标快照
```

V8.1 已完成：

```text
权重指标快照 → 环比 / 多周期均值 / 波动率 / 可用同比
```

V8.2 新增：

```text
权重指标快照 + 周期比较 → RAG 标准线命中
```

V8.2 仍然不做以下动作：

```text
不做联动比对
不做权重评分
不做升降权
不生成权重任务
不自动处罚运营
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

## 4. V8.0 / V8.1 / V8.2 数据表

```text
weight_metric_snapshots_v8
weight_metric_comparisons_v8
weight_rag_standard_hits_v8
```

`weight_rag_standard_hits_v8` 记录：

```text
hit_id
tenant_id
org_id
object_type
object_id
metric_name
standard_line
current_value
operator
hit_status
severity
consecutive_low_count
rule_id
domain
snapshot_version
comparison_direction
payload
created_at
```

## 5. V8.2 标准线命中

标准线状态：

```text
within_standard      达标
below_standard       低于标准线
above_risk_line      高于风险线
```

风险等级：

```text
正常
低
中
高
观察
```

当前覆盖三类对象：

```text
商品：ROI、点击率、转化率、毛利率、售后率、好评率
店铺：店铺 ROI、好评率、自然流量、点击率、商品健康率
运营：任务完成率、准时率、复盘质量分、证据完整度
```

运营对象的标准线命中只作为复核依据，不自动处罚、不自动降权、不自动变更权限。

## 6. 当前接口

```text
GET  /api/architecture/v8/weight-snapshots
POST /api/architecture/v8/weight-snapshots/generate
GET  /api/architecture/v8/weight-comparisons
POST /api/architecture/v8/weight-comparisons/generate
GET  /api/architecture/v8/weight-rag-hits
POST /api/architecture/v8/weight-rag-hits/generate
```

前端入口：

```text
权重中心
```

## 7. V8 后续节奏

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

## 8. V8 核心边界

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
