# 招聘展示版项目总结

## 项目名称

AI + RPA + ERP + CRM 电商经营自动化工作台 MVP

## 一句话介绍

基于电商 ERP / CRM 场景，设计并搭建一个 Workflow-first 的 AI 自动化工作台，用 Mock 经营数据跑通“数据导入 → AI 诊断 → RAG 召回 → RPA 任务草案 → 人工确认 → 报告输出”的业务闭环。

## 项目定位

该项目不是单纯的 AI 文案生成器，也不是无边界 Agent，而是面向真实企业流程的可控型 AI 工作流系统。

## 核心能力

- ERP 数据建模：商品、订单、库存、成本、活动价、退款。
- CRM 数据建模：客户、标签、RFM 分层、互动记录、售后敏感识别。
- AI 工作流：商品诊断、客户分层、售后归因、复盘建议。
- RAG 骨架：平台规则、合规风控、运营方法、客服 SOP。
- RPA 任务草案：日报、SKU 价格表、客户分层表、售后归因表。
- Human-in-the-loop：改价、投放、活动、客户触达等高风险动作必须人工确认。
- Evals：验证 CRM 分层、RPA 安全边界和人工确认逻辑。
- 前端 Demo：三段式展示导入数据、AI 诊断和 RPA 任务草案。

## 当前可运行内容

```bash
python -m src.run_demo
```

生成：

- outputs/product_diagnosis.json
- outputs/customer_segmentation.json
- outputs/rpa_task_draft.json
- outputs/rag_retrieval_context.json
- outputs/demo_report.md

```bash
python evals/run_evals.py
```

生成：

- evals/results/latest_results.json

静态前端：

```text
web_demo/index.html
```

## 简历表达

围绕电商 ERP / CRM 经营场景，设计并搭建 Workflow-first 的 AI 自动化运营工作台 MVP。项目通过 Mock 商品、订单、库存、退款、客户标签和互动数据，跑通数据导入、商品诊断、客户分层、RAG 召回、RPA 任务草案、人工确认和报告输出闭环；并通过 Evals 验证客户分层、RPA 安全边界和高风险动作人工确认机制，体现 AI 工作流、RAG、RPA、ERP / CRM 数据建模和产品风控能力。
