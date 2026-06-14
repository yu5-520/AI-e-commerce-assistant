# ERP 数据字段映射设计

## 1. 设计目标

ERP / 店铺后台 / Excel 表格的数据格式往往不统一。本文件用于定义 MVP 阶段的标准字段，方便后续进行数据导入、AI 诊断、RAG 检索、RPA 任务生成和日志回写。

MVP 阶段不直接连接真实 ERP API，优先使用 Mock CSV / Excel 数据模拟真实电商经营数据。

## 2. 数据源类型

```text
商品表 products
订单表 orders
库存表 inventory
退款表 refunds
活动表 campaigns
测试记录表 experiments
```

## 3. 商品表字段

| 标准字段 | 说明 | 示例 |
|---|---|---|
| product_id | 商品 ID | P001 |
| product_name | 商品名称 | 遮阳伞 |
| category | 商品类目 | 家居日用 |
| shop_type | 店铺类型 | 白牌 / 品牌 / 黑标 |
| cost_price | 成本价 | 10 |
| sale_price | 售价 | 29 |
| activity_price | 活动价 | 19.9 |
| shipping_cost | 物流成本 | 3 |
| stock | 当前库存 | 200 |
| supply_status | 货源状态 | 稳定 / 可补货 / 清仓 |
| is_sensitive_category | 是否敏感类目 | false |
| main_selling_points | 核心卖点 | 晴雨两用、骨架大、耐用 |

## 4. 订单表字段

| 标准字段 | 说明 | 示例 |
|---|---|---|
| order_id | 订单 ID | O20260614001 |
| product_id | 商品 ID | P001 |
| sku_id | SKU ID | SKU001 |
| order_time | 下单时间 | 2026-06-14 12:00 |
| quantity | 成交件数 | 1 |
| order_amount | 订单金额 | 29 |
| actual_paid | 实付金额 | 26.9 |
| refund_status | 退款状态 | none / refunded / partial |
| traffic_source | 流量来源 | 自然搜索 / 活动 / 付费 |

## 5. 库存表字段

| 标准字段 | 说明 | 示例 |
|---|---|---|
| snapshot_id | 库存快照 ID | INV001 |
| product_id | 商品 ID | P001 |
| sku_id | SKU ID | SKU001 |
| current_stock | 当前库存 | 200 |
| available_stock | 可售库存 | 180 |
| safety_stock | 安全库存线 | 50 |
| supply_status | 货源状态 | 稳定 |
| updated_at | 更新时间 | 2026-06-14 12:00 |

## 6. 退款表字段

| 标准字段 | 说明 | 示例 |
|---|---|---|
| refund_id | 退款 ID | R001 |
| order_id | 订单 ID | O20260614001 |
| product_id | 商品 ID | P001 |
| refund_amount | 退款金额 | 29 |
| refund_reason | 退款原因 | 质量问题 / 不喜欢 / 尺寸不符 |
| refund_time | 退款时间 | 2026-06-15 10:00 |
| after_sale_note | 售后备注 | 用户反馈骨架不够稳 |

## 7. 活动表字段

| 标准字段 | 说明 | 示例 |
|---|---|---|
| campaign_id | 活动 ID | C001 |
| product_id | 商品 ID | P001 |
| campaign_type | 活动类型 | 秒杀 / 限时折扣 / 平台活动 |
| campaign_price | 活动价 | 19.9 |
| campaign_stock | 活动库存 | 100 |
| start_time | 开始时间 | 2026-06-20 |
| end_time | 结束时间 | 2026-06-23 |
| expected_margin | 预计毛利 | 6.9 |
| risk_notes | 风险备注 | 活动价接近保本线 |

## 8. 测试记录字段

| 标准字段 | 说明 | 示例 |
|---|---|---|
| experiment_id | 测试 ID | E001 |
| product_id | 商品 ID | P001 |
| title_version | 标题版本 | T001 |
| image_plan | 主图方案 | IMG001 |
| sku_plan | SKU 方案 | SKU_PLAN001 |
| sale_price | 测试售价 | 29 |
| exposure | 曝光 | 1000 |
| clicks | 点击 | 80 |
| click_rate | 点击率 | 0.08 |
| orders | 成交数 | 5 |
| conversion_rate | 转化率 | 0.0625 |
| ad_spend | 推广花费 | 30 |
| roi | ROI | 2.1 |
| user_notes | 用户备注 | 点击正常，转化一般 |

## 9. AI 诊断输入映射

AI 诊断时优先读取：

```text
商品基础信息
+ 成本 / 售价 / 活动价
+ SKU 结构
+ 库存快照
+ 订单摘要
+ 退款原因
+ 历史测试记录
+ 平台规则 / 合规知识
```

## 10. RPA 任务生成输入映射

RPA 任务生成时优先读取：

```text
商品 ID
任务类型
AI 建议
用户确认状态
执行所需字段
执行风险等级
回写目标
```

## 11. 字段映射结论

MVP 阶段不追求接入所有 ERP，而是先把字段结构标准化。

> 只要商品、订单、库存、退款、活动、测试记录能被统一建模，后续就可以接入不同 ERP、表格或店铺后台导出数据。
