# CRM 客户分层工作流

## 1. 输入数据

- mock_customers.csv
- mock_customer_tags.csv
- mock_interactions.csv
- mock_orders.csv
- mock_refunds.csv

## 2. 工作流

```text
导入脱敏客户数据
↓
校验 customer_id 与订单 / 互动记录关联
↓
计算 RFM 与基础客户指标
↓
识别客户标签：高价值、新客、沉睡、流失风险、售后敏感
↓
RAG 召回客户运营方法、客服 SOP 和合规触达规则
↓
AI 生成客户分层报告
↓
生成 CRM 任务草案
↓
人工确认
↓
RPA 导出客户分层表和任务清单
↓
日志回写
```

## 3. AI 输出要求

AI 输出必须包含：

- 客户分层
- 分层依据
- 推荐动作
- 风险提示
- 是否需要人工确认
- 是否允许 RPA 执行

## 4. 安全边界

不自动触达真实客户，不自动群发，不自动承诺优惠，不自动处理退款。
