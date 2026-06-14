# 架构升级变更记录

## 1. 原始定位

项目最初定位为拼多多 AI 商品增长工作台，重点围绕商品档案、标题、主图、SKU、活动和投放建议形成 AI 商品运营辅助能力。

## 2. 第一轮升级：ERP / RPA

升级为 AI + RPA 电商运营自动化工作台。

新增：

- ERP 数据字段映射
- RPA 工作流场景
- Human-in-the-loop 人工确认机制
- Mock ERP 数据
- RAG 架构设计

核心变化：

> 从“AI 生成方案”升级为“ERP 数据输入 → AI 诊断 → RPA 任务草案 → 人工确认 → 日志回写”。

## 3. 第二轮升级：CRM

升级为 AI + RPA + ERP + CRM 电商经营自动化工作台。

新增：

- CRM 分析文档
- CRM 数据模型
- 客户分层设计
- Mock 客户数据
- 客户标签数据
- 互动记录数据
- 售后归因工作流

核心变化：

> ERP 管货，CRM 管人，AI 同时处理商品经营和客户经营问题。

## 4. 第三轮升级：Workflow-first 与 Agent 边界

新增 workflow-vs-agent-boundary.md。

明确：

- 当前不是深度自治 Agent。
- 当前是多系统连接型 AI 工作流。
- 未来可以在低风险环节 Agent-ready。
- 高风险动作不交给 Agent 自主执行。

## 5. 第四轮升级：工程化骨架

新增：

- schemas/
- prompts/
- workflows/
- evals/
- knowledge_base/

核心变化：

> 从“架构可讲”升级为“输入输出有契约、Prompt 有边界、Evals 可验证”。

## 6. 第五轮升级：可运行 Mock Workflow

新增：

- src/run_demo.py
- src/data_loader/
- src/diagnosis/
- src/rag/
- src/rpa_tasks/
- src/approval/
- src/reports/
- evals/run_evals.py

核心变化：

> 从“文档项目”升级为“可运行 Mock Workflow 项目”。

## 7. 第六轮升级：前端三段式 Demo

新增：

- web_demo/index.html
- web_demo/styles.css
- web_demo/app.js
- web_demo/sample-output/
- docs/frontend-demo-design.md

核心变化：

> 从命令行可运行，升级为可以在浏览器中展示“导入数据 → AI 诊断 → RPA 任务草案 → 人工确认项”的可视化流程。

## 8. 当前最终定位

> AI + RPA + ERP + CRM 电商经营自动化工作台 MVP。

一句话：

> 数据进入系统，RAG 给依据，AI 做判断，人工控风险，RPA 做低风险执行，日志做复盘。
