# 领域模型

## 1. 设计目标

领域模型用于定义产品中的核心业务对象，以及它们之间的关系。

当前目标不是设计完整数据库，而是先把产品中的对象边界摸清楚，避免后续 API、页面和数据结构混乱。

## 2. 核心对象总览

```text
Product 商品
Order 订单
Inventory 库存
Refund 退款 / 售后
Customer 客户
Interaction 客户互动
KnowledgeChunk 知识片段
Diagnosis 诊断
Task 任务草案
Approval 审批记录
Report 报告
WorkflowRun 工作流运行记录
ExecutionLog 执行日志
```

## 3. 商品域

### 3.1 Product 商品

描述一个可运营商品。

关键字段：

```text
product_id
product_name
category
shop_type
cost_price
sale_price
activity_price
shipping_cost
stock
supply_status
is_sensitive_category
main_selling_points
```

关联对象：

```text
Product 1 - N Order
Product 1 - N InventorySnapshot
Product 1 - N Refund
Product 1 - N Diagnosis
Product 1 - N Task
Product 1 - N Report
```

### 3.2 Order 订单

描述商品成交记录。

关键字段：

```text
order_id
product_id
customer_id
quantity
actual_paid
order_channel
order_time
refund_status
```

### 3.3 Inventory 库存

描述商品库存状态。

关键字段：

```text
product_id
available_stock
locked_stock
warning_line
supply_status
updated_at
```

### 3.4 Refund 退款 / 售后

描述退款和售后问题。

关键字段：

```text
refund_id
order_id
product_id
customer_id
refund_reason
refund_amount
after_sales_note
created_at
```

## 4. 客户域

### 4.1 Customer 客户

描述脱敏客户档案。

关键字段：

```text
customer_id
nickname_hash
first_order_time
last_order_time
total_orders
total_amount
refund_count
customer_level
rfm_score
```

关联对象：

```text
Customer 1 - N Order
Customer 1 - N Interaction
Customer 1 - N Refund
Customer 1 - N CustomerTag
Customer 1 - N Diagnosis
Customer 1 - N Task
```

### 4.2 CustomerTag 客户标签

描述客户分层和状态。

关键字段：

```text
tag_id
customer_id
tag_name
tag_source
confidence
created_at
```

典型标签：

```text
高价值客户
新客
沉睡客户
售后敏感客户
复购潜力客户
流失风险客户
价格敏感客户
活动敏感客户
```

### 4.3 Interaction 客户互动

描述客户咨询、售后、活动提醒和客服记录。

关键字段：

```text
interaction_id
customer_id
interaction_type
channel
content_summary
sentiment
created_at
```

## 5. 知识域

### 5.1 KnowledgeChunk 知识片段

描述 RAG 可召回的知识单元。

关键字段：

```text
chunk_id
source_type
title
content
tags
risk_level
source_uri
updated_at
```

知识类型：

```text
平台规则
合规风控
运营方法
客服 SOP
商品历史
客户历史
```

## 6. 诊断域

### 6.1 Diagnosis 诊断

描述一次 AI / 规则诊断结果。

关键字段：

```text
diagnosis_id
target_type      product | customer | campaign | after_sales
target_id
input_snapshot
rag_context
conclusion
risk_level
basis
suggested_actions
requires_approval
created_at
```

诊断类型：

```text
商品诊断
SKU 利润诊断
库存预警
客户分层
售后归因
活动准备诊断
```

## 7. 任务域

### 7.1 Task 任务草案

描述由 AI 诊断生成的可执行任务草案。

关键字段：

```text
task_id
task_type
target_product_id
target_customer_segment
risk_level
requires_approval
auto_execution_allowed
approval_status
status
ai_suggestion
execution_result
created_at
updated_at
```

任务状态：

```text
draft
pending_approval
approved
rejected
running
success
failed
rollback_required
```

任务类型：

```text
daily_report
sku_price_table
activity_prepare_table
customer_segmentation_report
retention_task_list
after_sales_analysis
review_iteration_report
```

### 7.2 Approval 审批记录

描述用户对任务草案的确认、拒绝、修改或暂存。

关键字段：

```text
approval_id
task_id
user_id
action_type
risk_level
ai_reason
risk_notes
approval_status
approved_at
```

审批状态：

```text
pending
approved
rejected
modified
saved_draft
```

## 8. 报告域

### 8.1 Report 报告

描述最终输出给用户的结果。

关键字段：

```text
report_id
report_type
target_type
target_id
content
source_diagnosis_ids
source_task_ids
created_at
export_format
```

报告类型：

```text
商品诊断报告
客户分层报告
售后归因报告
经营日报
SKU 价格建议表
复盘报告
```

## 9. 工作流域

### 9.1 WorkflowRun 工作流运行记录

描述一次完整工作流运行。

关键字段：

```text
workflow_run_id
workflow_type
input_files
input_snapshot
status
started_at
finished_at
error_message
```

### 9.2 ExecutionLog 执行日志

描述每个节点的执行记录。

关键字段：

```text
log_id
workflow_run_id
node_name
input_snapshot
output_snapshot
status
created_at
```

## 10. 对象关系总图

```text
Product ── Order ── Customer
   │          │          │
   │          │          ├── CustomerTag
   │          │          └── Interaction
   │          │
   ├── Inventory
   ├── Refund
   └── Diagnosis
          │
          ├── KnowledgeChunk
          └── Task
                │
                ├── Approval
                └── Report

WorkflowRun ── ExecutionLog
```

## 11. 当前 MVP 的最小对象

当前阶段必须先跑通：

```text
Product
Customer
Diagnosis
Task
Approval
Report
WorkflowRun
ExecutionLog
```

订单、库存、退款、互动作为诊断输入存在，后续再扩展为完整管理对象。
