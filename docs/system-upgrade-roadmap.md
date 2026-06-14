# 系统架构升级路线：垂直类目货架电商经营循环

## 1. 升级目标

当前仓库已经具备 **ERP + CRM 经营判断底座**，下一步不是继续堆泛功能，而是把系统升级成：

> **面向垂直类目的 AI 货架电商经营循环系统。**

目标闭环：

```text
垂直类目知识层
↓
ERP + CRM 经营判断系统
↓
同类目竞品比对系统
↓
同类目上新增长系统
↓
流量测试与数据回流系统
↓
再次进入 ERP + CRM 经营判断
```

## 2. 为什么要这样升级

真实货架电商不是跨类目乱铺，而是越来越垂直。

老板真正能理解和赚钱的，是自己熟悉的垂直类目：

```text
供应链
价格带
季节性
主图表达
SKU 结构
竞品打法
退货原因
客服话术
活动节奏
```

因此，系统不能先假设“全类目通用”，而要先跑通一个垂直类目样板，再复制到第二个类目。

## 3. 当前状态：V0.8

当前已完成：

```text
Mock ERP / CRM 数据
数据导入校验
商品经营诊断
CRM 客户分层
轻量 RAG 召回
RPA 任务草案
人工审批
报告与日志
FastAPI 后端
web_demo 前端
最小 Evals
```

当前主入口：

```text
python -m src.run_demo
uvicorn src.api.main:app --reload
http://127.0.0.1:8000/
```

当前系统本质：

> 已有商品经营判断 + 表格文档运营自动化底座。

## 4. V0.9：垂直类目配置层

### 目标

让系统从泛电商判断升级为垂直类目判断。

### 新增目录

```text
src/category/
  category_profile_loader.py
  category_rules.py
  category_context.py

knowledge_base/category_profiles/
  sun_protection_clothing.md

examples/category_sun_protection/
  mock_products.csv
  mock_orders.csv
  mock_inventory.csv
  mock_refunds.csv
  mock_competitors.csv
  mock_customer_feedback.csv
  mock_traffic_tests.csv
```

### 核心字段

```text
category_id
category_name
seasonality
price_bands
target_customers
main_selling_points
common_return_reasons
high_risk_claims
image_expression_rules
sku_structure_rules
competitor_compare_dimensions
traffic_test_metrics
```

### 验收标准

- 能读取一个垂直类目知识档案。
- 商品诊断能拿到类目上下文。
- RAG 能召回类目知识片段。
- 输出报告能说明当前判断基于哪个类目。

## 5. V1.0：同类目竞品比对系统

### 目标

经营判断发现问题后，能围绕同类目竞品做差距分析。

### 新增目录

```text
src/competitor/
  competitor_loader.py
  price_compare.py
  title_compare.py
  image_selling_point_compare.py
  sku_compare.py
  review_gap_analysis.py
  competitor_report.py
```

### Mock 数据

```text
examples/mock_competitors.csv
```

### 字段建议

```text
competitor_id
category
product_name
price
activity_price
sales_estimate
review_count
bad_review_keywords
title_keywords
main_image_selling_points
sku_structure
shipping_promise
after_sales_issue
```

### 核心输出

```text
价格带差距
标题关键词差距
主图卖点差距
SKU 结构差距
差评机会
售后风险差异
是否建议优化老品
是否建议扩相似新品
```

### 触发逻辑

```text
点击低 → 比对竞品主图 / 标题
转化低 → 比对竞品价格 / SKU / 评价
退款高 → 比对竞品差评 / 卖点承诺
库存高 → 比对竞品活动价 / 清货打法
类目表现好 → 找相似品扩品
```

## 6. V1.1：同类目上新增长系统

### 目标

从已有经营数据、竞品差距和供应链货盘里生成上新方案。

### 新增目录

```text
src/listing/
  new_product_candidate.py
  listing_draft_generator.py
  title_plan.py
  image_plan.py
  sku_plan.py
  pricing_plan.py
  compliance_checklist.py
```

### Mock 数据

```text
examples/mock_supplier_products.csv
examples/mock_listing_drafts.csv
```

### 核心能力

```text
从供应链货盘筛选新品
判断是否符合当前垂直类目
判断利润空间
判断库存承接
判断竞品差异化机会
生成标题草案
生成主图文案草案
生成 SKU 草案
生成上架字段草案
生成合规检查表
```

### 安全边界

上新系统只生成资料，不自动上架。

```text
自动生成上新资料
人工确认
再由商家执行或进入低风险 RPA 草案
```

## 7. V1.2：流量测试与数据回流系统

### 目标

上新或优化后必须进入测试，否则只是一次性生成。

### 新增目录

```text
src/traffic_test/
  experiment_plan.py
  ab_test_table.py
  traffic_metrics.py
  test_result_diagnosis.py
  next_action_decision.py
```

### Mock 数据

```text
examples/mock_traffic_experiments.csv
```

### 字段建议

```text
experiment_id
product_id
title_version
image_version
sku_version
test_price
traffic_source
impressions
clicks
orders
conversion_rate
refund_count
roi
test_status
next_action
```

### 核心判断

```text
点击低：标题 / 主图问题
点击高转化低：价格 / SKU / 详情承接问题
转化高退款高：卖点承诺 / 质量 / 尺码 / 物流问题
ROI 低：投放节奏或价格带问题
库存消耗慢：清货或换款
```

### 输出

```text
继续测试
换标题
换主图
调 SKU
调价格
放量
止损
扩品
进入售后归因
```

## 8. V1.3：完整经营循环系统

### 目标

形成完整闭环：

```text
经营判断
↓
发现问题 / 机会
↓
竞品比对
↓
优化现有商品 or 上新增长
↓
小流量测试
↓
数据回流
↓
再次经营判断
```

### 扩展方向

- 支持第二个垂直类目。
- 支持多类目配置隔离。
- 支持多版本测试记录。
- 支持长期商品运营档案。
- 支持更完整报告中心。

## 9. RPA 升级方向

RPA 不优先接真实平台后台，而是先升级为运营文档流转层。

新增目录：

```text
src/rpa_documents/
  daily_report.py
  competitor_report.py
  listing_checklist.py
  traffic_test_report.py
  weekly_review.py
```

RPA 优先生成：

```text
经营日报
周报
SKU 建议表
竞品比对报告
上新检查表
流量测试表
测试复盘报告
审批流记录
```

## 10. 数据模型升级

当前 SQLite 主要记录 workflow、log、approval、report。

后续应补业务表：

```text
products
category_profiles
competitors
supplier_products
listing_drafts
traffic_experiments
customer_segments
after_sales_cases
operation_tasks
business_reports
```

目标是从“跑一次 workflow”升级为“长期经营档案”。

## 11. 前端升级方向

新增页面顺序：

```text
1. 经营总览
2. 垂直类目配置
3. ERP / CRM 经营判断
4. 竞品比对
5. 上新增长
6. 流量测试
7. 任务审批
8. 报告日志
```

页面叙事：

```text
先看现有商品
↓
再看问题商品
↓
再看竞品差距
↓
再生成优化 / 上新方案
↓
再看测试结果
↓
再回到经营判断
```

## 12. 总结

下一阶段不是继续堆 RPA，而是把系统从：

> 已有商品经营内勤

升级为：

> 垂直类目驱动的货架电商经营循环。

最小正确路线：

```text
V0.8：ERP + CRM 经营判断系统
V0.9：垂直类目配置层
V1.0：同类目竞品比对系统
V1.1：同类目上新增长系统
V1.2：流量测试与数据回流
V1.3：完整货架电商经营循环系统
```
