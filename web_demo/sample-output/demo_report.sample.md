# Demo Report Sample

## 1. 商品经营诊断

### P001 - 遮阳伞

- 风险等级：medium
- 风险标签：high_inventory_low_order_risk, activity_price_margin_risk
- 建议动作：生成 SKU 价格建议表；活动报名前人工确认

### P003 - 护腰坐垫

- 风险等级：high
- 风险标签：sensitive_category_compliance_risk, refund_abnormal_risk
- 建议动作：进入售后归因工作流；先做合规检查

## 2. CRM 客户分层

### C001 - 高价值客户

- 标签：高价值，复购潜力
- 建议动作：生成老客复购任务草案

### C004 - 售后敏感客户

- 标签：售后敏感，流失风险
- 建议动作：优先生成售后归因表，不直接营销触达

## 3. RPA 任务草案

- TASK_PRODUCT_DAILY_001：生成商品经营日报
- TASK_SKU_PRICE_001：生成 SKU 价格建议表
- TASK_CRM_AFTER_SALES_004：生成售后归因表

## 4. 人工确认边界

所有中高风险任务均为 pending_approval，auto_execution_allowed=false。
