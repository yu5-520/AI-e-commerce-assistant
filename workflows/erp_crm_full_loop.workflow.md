# ERP + CRM 全链路电商经营工作流

## 1. 输入数据

- examples/mock_products.csv
- examples/mock_orders.csv
- examples/mock_inventory.csv
- examples/mock_refunds.csv
- examples/mock_customers.csv
- examples/mock_customer_tags.csv
- examples/mock_interactions.csv

## 2. 总流程

```text
导入 ERP / CRM Mock 数据
↓
字段映射与数据清洗
↓
建立商品档案与客户档案
↓
RAG 召回商品历史、客户历史、平台规则、合规边界、运营方法和客服 SOP
↓
AI 商品诊断：SKU利润、库存、订单、退款、活动风险
↓
AI 客户诊断：客户分层、复购判断、流失预警、售后敏感识别
↓
生成经营建议与 RPA 任务草案
↓
风险分级
↓
Human-in-the-loop 人工确认
↓
RPA 执行低风险任务
↓
保存 AI 报告、RAG 召回日志、确认记录、RPA 执行日志
↓
生成下一轮复盘动作
```

## 3. 工作流节点

### 3.1 数据导入节点

校验：

- product_id 是否可关联
- customer_id 是否脱敏
- order_id 是否完整
- 成本、售价、库存是否缺失
- 退款原因是否可归类

### 3.2 AI 商品诊断节点

输出：

- 商品经营状态
- SKU 利润风险
- 库存风险
- 订单 / 退款异常
- 活动适配度
- 下一步商品运营建议

### 3.3 AI 客户诊断节点

输出：

- 客户分层
- 复购可能性
- 流失风险
- 售后敏感度
- 客户运营任务草案

### 3.4 RPA 任务草案节点

可生成：

- 运营日报
- SKU 价格建议表
- 活动准备表
- 客户分层表
- 复购任务表
- 售后归因表
- 复盘报告

### 3.5 人工确认节点

必须展示：

- AI 建议依据
- RAG 召回依据
- 风险等级
- 是否涉及资金或客户触达
- 是否允许 RPA 执行

### 3.6 日志回写节点

保存：

- AI 输入快照
- AI 输出报告
- RAG 召回记录
- 用户确认记录
- RPA 执行日志
- 失败原因和人工处理建议

## 4. 安全边界

该工作流不自动执行：

- 改价
- 上架 / 下架
- 投放
- 活动报名
- 客户群发
- 退款处理
- 诱导好评
- 平台风控绕过

## 5. 设计结论

本工作流体现 Workflow-first 原则：

> 数据进入系统，AI 做判断，RAG 给依据，人工控风险，RPA 做低风险执行，日志做复盘。
