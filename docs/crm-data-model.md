# CRM 数据模型设计

## 1. 设计目标

CRM 数据模型用于保存脱敏客户档案、客户标签、互动记录、客户分层和客户运营任务。

MVP 阶段只使用 Mock 数据，不保存真实姓名、手机号、微信号、地址等隐私信息。

## 2. crm_customers 客户表

```sql
CREATE TABLE crm_customers (
  customer_id TEXT PRIMARY KEY,
  nickname_hash TEXT,
  first_order_time DATETIME,
  last_order_time DATETIME,
  total_orders INTEGER,
  total_amount REAL,
  refund_count INTEGER,
  last_interaction_time DATETIME,
  customer_level TEXT,
  rfm_score TEXT,
  created_at DATETIME,
  updated_at DATETIME
);
```

字段说明：

| 字段 | 说明 |
|---|---|
| customer_id | 脱敏客户 ID |
| nickname_hash | 昵称哈希，不保存真实昵称 |
| first_order_time | 首单时间 |
| last_order_time | 最近购买时间 |
| total_orders | 累计订单数 |
| total_amount | 累计消费金额 |
| refund_count | 退款次数 |
| last_interaction_time | 最近互动时间 |
| customer_level | 客户等级 |
| rfm_score | RFM 评分 |

## 3. crm_customer_tags 客户标签表

```sql
CREATE TABLE crm_customer_tags (
  tag_id TEXT PRIMARY KEY,
  customer_id TEXT NOT NULL,
  tag_name TEXT,
  tag_source TEXT,
  confidence REAL,
  created_at DATETIME,
  FOREIGN KEY (customer_id) REFERENCES crm_customers(customer_id)
);
```

常见标签：

- 高价值客户
- 新客
- 沉睡客户
- 价格敏感
- 活动敏感
- 售后敏感
- 复购潜力
- 流失风险

## 4. crm_interactions 客户互动表

```sql
CREATE TABLE crm_interactions (
  interaction_id TEXT PRIMARY KEY,
  customer_id TEXT NOT NULL,
  interaction_type TEXT,
  channel TEXT,
  content_summary TEXT,
  sentiment TEXT,
  created_at DATETIME,
  FOREIGN KEY (customer_id) REFERENCES crm_customers(customer_id)
);
```

互动类型：

- 客服咨询
- 售后反馈
- 优惠券触达
- 活动提醒
- 复购提醒
- 投诉反馈

## 5. crm_segments 客户分群表

```sql
CREATE TABLE crm_segments (
  segment_id TEXT PRIMARY KEY,
  segment_name TEXT,
  segment_rule TEXT,
  customer_count INTEGER,
  recommended_action TEXT,
  risk_level TEXT,
  created_at DATETIME
);
```

示例分群：

- 高价值复购客户
- 30 天未复购客户
- 90 天沉睡客户
- 售后敏感客户
- 活动敏感客户
- 流失风险客户

## 6. crm_campaigns 客户运营活动表

```sql
CREATE TABLE crm_campaigns (
  campaign_id TEXT PRIMARY KEY,
  campaign_name TEXT,
  target_segment TEXT,
  campaign_goal TEXT,
  message_template TEXT,
  coupon_strategy TEXT,
  approval_status TEXT,
  execution_status TEXT,
  created_at DATETIME,
  updated_at DATETIME
);
```

注意：MVP 阶段只生成活动草案，不自动触达真实客户。

## 7. crm_tasks CRM 自动化任务表

```sql
CREATE TABLE crm_tasks (
  task_id TEXT PRIMARY KEY,
  customer_segment TEXT,
  task_type TEXT,
  ai_suggestion TEXT,
  requires_approval BOOLEAN DEFAULT true,
  approval_status TEXT DEFAULT 'pending',
  rpa_execution_status TEXT DEFAULT 'draft',
  result_summary TEXT,
  created_at DATETIME,
  updated_at DATETIME
);
```

任务类型：

- customer_segmentation_report
- retention_task_list
- after_sales_analysis
- coupon_strategy_draft
- customer_message_draft
- crm_daily_report

## 8. CRM 与 ERP 的关联

CRM 与 ERP 通过订单数据关联：

```text
crm_customers.customer_id
↓
erp_orders.customer_id
↓
erp_products.product_id
```

这样可以分析：

- 哪类客户买了什么商品
- 哪类商品带来高价值客户
- 哪类商品售后风险高
- 哪类客户对活动价敏感
- 哪些客户适合复购运营

## 9. 隐私边界

MVP 阶段：

- 不保存真实姓名
- 不保存手机号
- 不保存微信号
- 不保存详细地址
- 不保存支付敏感信息
- 不自动触达真实客户

## 10. 设计结论

CRM 数据模型的核心不是“营销群发”，而是支持 AI 做客户分层、复购判断、售后归因和客户运营任务草案。

> 客户数据必须脱敏，客户触达必须人工确认。
