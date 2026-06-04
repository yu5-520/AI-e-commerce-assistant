# 数据模型设计

## 1. 设计原则

本产品的数据模型围绕“商品档案”展开。

核心原则：

- 一个商品对应一个长期运营档案。
- 标题、主图、SKU、活动、投放都要有版本记录。
- 每一轮测试都要能追溯当时用了什么标题、主图、价格、SKU 和投放策略。
- AI 复盘必须基于历史数据，而不是每次重新生成。
- 涉及敏感类目和高风险表达时，需要保存风险标记。

## 2. 核心实体关系

```text
User
↓
Product
↓
Asset / TitleVersion / ImagePlan / SKUPlan / Competitor / Experiment / AIReport
```

一个用户可以创建多个商品。

一个商品可以拥有多个标题版本、主图方案、SKU 方案、竞品记录、测试记录和 AI 报告。

## 3. User 用户表

用于保存用户基础信息和套餐权限。

```sql
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  nickname TEXT,
  email TEXT,
  plan TEXT DEFAULT 'free',
  usage_count INTEGER DEFAULT 0,
  created_at DATETIME,
  updated_at DATETIME
);
```

建议字段：

| 字段 | 说明 |
|---|---|
| id | 用户 ID |
| nickname | 用户昵称 |
| email | 邮箱 |
| plan | 套餐类型 |
| usage_count | AI 使用次数 |
| created_at | 创建时间 |
| updated_at | 更新时间 |

## 4. Product 商品表

商品表是核心主表。

```sql
CREATE TABLE products (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  name TEXT NOT NULL,
  category TEXT,
  cost_price REAL,
  sale_price REAL,
  shipping_cost REAL,
  stock INTEGER,
  supply_status TEXT,
  shop_type TEXT,
  has_brand_auth BOOLEAN DEFAULT FALSE,
  has_black_label BOOLEAN DEFAULT FALSE,
  is_sensitive_category BOOLEAN DEFAULT FALSE,
  current_route TEXT,
  status TEXT DEFAULT 'testing',
  created_at DATETIME,
  updated_at DATETIME,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
```

建议字段：

| 字段 | 说明 |
|---|---|
| id | 商品 ID |
| user_id | 所属用户 |
| name | 商品名称 |
| category | 商品类目 |
| cost_price | 成本价 |
| sale_price | 售价 |
| shipping_cost | 物流成本 |
| stock | 库存 |
| supply_status | 货源状态，如稳定、可补货、清仓 |
| shop_type | 店铺类型，如白牌、品牌、黑标 |
| has_brand_auth | 是否有品牌授权 |
| has_black_label | 是否黑标 |
| is_sensitive_category | 是否敏感类目 |
| current_route | 当前推荐路线 |
| status | 商品状态，如 testing、scaling、paused、stopped |

## 5. Asset 素材表

保存商品图片和素材分析结果。

```sql
CREATE TABLE assets (
  id TEXT PRIMARY KEY,
  product_id TEXT NOT NULL,
  asset_type TEXT,
  file_url TEXT,
  usage_scene TEXT,
  ai_summary TEXT,
  risk_level TEXT DEFAULT 'low',
  risk_notes TEXT,
  created_at DATETIME,
  FOREIGN KEY (product_id) REFERENCES products(id)
);
```

素材类型：

- main_image：主图
- white_background：白底图
- detail_image：详情图
- real_photo：实拍图
- competitor_screenshot：竞品截图
- activity_image：活动图

## 6. TitleVersion 标题版本表

保存 AI 生成和用户实际使用过的标题。

```sql
CREATE TABLE title_versions (
  id TEXT PRIMARY KEY,
  product_id TEXT NOT NULL,
  title TEXT NOT NULL,
  title_type TEXT,
  keywords TEXT,
  stage TEXT,
  test_goal TEXT,
  matched_image_plan_id TEXT,
  risk_notes TEXT,
  status TEXT DEFAULT 'generated',
  created_at DATETIME,
  FOREIGN KEY (product_id) REFERENCES products(id)
);
```

标题类型：

- search_coverage：搜索词覆盖型
- low_price：低价刺激型
- function_selling_point：功能卖点型
- scene_user：场景人群型
- activity：活动承接型
- long_tail：长尾关键词型
- competitor_capture：竞品承接型
- safe：安全保守型

## 7. ImagePlan 主图方案表

保存主图文案和构图方案，不一定保存真实图片。

```sql
CREATE TABLE image_plans (
  id TEXT PRIMARY KEY,
  product_id TEXT NOT NULL,
  plan_name TEXT,
  main_text TEXT,
  sub_text TEXT,
  layout_suggestion TEXT,
  product_position_suggestion TEXT,
  matched_title_type TEXT,
  matched_sku_id TEXT,
  test_goal TEXT,
  risk_notes TEXT,
  status TEXT DEFAULT 'generated',
  created_at DATETIME,
  FOREIGN KEY (product_id) REFERENCES products(id)
);
```

主图方案类型：

- low_price_impact：低价冲击版
- function_selling_point：功能卖点版
- pain_point：痛点解决版
- scene：场景使用版
- specification_compare：规格对比版
- activity：活动承接版
- competitor_difference：竞品差异版

## 8. SKUPlan 表

保存 SKU 组合和利润测算结果。

```sql
CREATE TABLE sku_plans (
  id TEXT PRIMARY KEY,
  product_id TEXT NOT NULL,
  sku_name TEXT,
  sku_role TEXT,
  cost_price REAL,
  sale_price REAL,
  shipping_cost REAL,
  activity_price REAL,
  estimated_ad_cost REAL,
  estimated_refund_loss REAL,
  gross_profit REAL,
  break_even_price REAL,
  risk_notes TEXT,
  is_main_sku BOOLEAN DEFAULT FALSE,
  created_at DATETIME,
  FOREIGN KEY (product_id) REFERENCES products(id)
);
```

SKU 角色：

- traffic：引流款
- profit：利润款
- bundle：组合款
- activity：活动款
- clearance：清货款

## 9. Competitor 竞品表

保存竞品信息和爆品拆解结果。

```sql
CREATE TABLE competitors (
  id TEXT PRIMARY KEY,
  product_id TEXT NOT NULL,
  competitor_name TEXT,
  competitor_url TEXT,
  price REAL,
  activity_price REAL,
  title TEXT,
  image_summary TEXT,
  sku_summary TEXT,
  selling_points TEXT,
  review_pain_points TEXT,
  opportunity_notes TEXT,
  infringement_risk_notes TEXT,
  created_at DATETIME,
  FOREIGN KEY (product_id) REFERENCES products(id)
);
```

## 10. Experiment 测试记录表

保存每一轮运营测试数据。

```sql
CREATE TABLE experiments (
  id TEXT PRIMARY KEY,
  product_id TEXT NOT NULL,
  round_name TEXT,
  title_version_id TEXT,
  image_plan_id TEXT,
  sku_plan_id TEXT,
  sale_price REAL,
  exposure INTEGER,
  clicks INTEGER,
  click_rate REAL,
  orders INTEGER,
  conversion_rate REAL,
  revenue REAL,
  ad_spend REAL,
  roi REAL,
  refunds INTEGER,
  user_notes TEXT,
  ai_conclusion TEXT,
  next_action TEXT,
  created_at DATETIME,
  FOREIGN KEY (product_id) REFERENCES products(id)
);
```

测试记录是复盘引擎的核心输入。

## 11. AIReport AI 报告表

保存所有 AI 输出结果。

```sql
CREATE TABLE ai_reports (
  id TEXT PRIMARY KEY,
  product_id TEXT NOT NULL,
  report_type TEXT,
  input_snapshot TEXT,
  output_content TEXT,
  structured_output TEXT,
  risk_level TEXT DEFAULT 'low',
  created_at DATETIME,
  FOREIGN KEY (product_id) REFERENCES products(id)
);
```

报告类型：

- route_judgement
- title_variation
- image_plan
- sku_profit
- competitor_analysis
- paid_test
- activity_prepare
- review_decision
- compliance_check

## 12. ComplianceCheck 合规检查表

保存敏感类目和高风险表达的检查结果。

```sql
CREATE TABLE compliance_checks (
  id TEXT PRIMARY KEY,
  product_id TEXT NOT NULL,
  check_type TEXT,
  risk_level TEXT,
  risky_terms TEXT,
  risk_description TEXT,
  suggested_replacement TEXT,
  action_required TEXT,
  created_at DATETIME,
  FOREIGN KEY (product_id) REFERENCES products(id)
);
```

风险等级：

- low：低风险
- medium：中风险
- high：高风险
- blocked：禁止输出或不建议继续

## 13. 推荐的 MVP 数据表

第一版 MVP 最少只需要：

1. users
2. products
3. title_versions
4. image_plans
5. sku_plans
6. experiments
7. ai_reports

后续再增加：

- assets
- competitors
- compliance_checks

## 14. 数据闭环

核心闭环：

```text
Product
↓
TitleVersion + ImagePlan + SKUPlan
↓
Experiment
↓
AIReport(review_decision)
↓
下一轮 TitleVersion / ImagePlan / SKUPlan
```

产品真正的价值来自这个闭环，而不是单次 AI 生成。

## 15. 数据模型结论

本产品的数据结构应该优先服务于“商品级长期运营记忆”。

只要每一轮标题、主图、SKU、价格、投放和测试数据能沉淀下来，后续 AI 才能从文案生成器升级为商品增长助手。
