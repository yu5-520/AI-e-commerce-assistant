# Reviewer Guide

## 1. 先看什么？

建议按这个顺序查看：

1. README.md
2. docs/demo-runbook.md
3. web_demo/index.html
4. src/run_demo.py
5. evals/run_evals.py
6. docs/recruiter-project-summary.md

## 2. 项目是什么？

这是一个 Workflow-first 的 AI + RPA + ERP + CRM 电商经营自动化工作台 MVP。

它不是生产级系统，也不是无边界 Agent。

## 3. 怎么运行？

```bash
python -m src.run_demo
python evals/run_evals.py
```

前端：

```text
web_demo/index.html
```

## 4. 看什么结果？

- outputs/product_diagnosis.json
- outputs/customer_segmentation.json
- outputs/rpa_task_draft.json
- outputs/demo_report.md
- evals/results/latest_results.json

## 5. 重点判断

这个项目重点展示：

- AI 工作流设计
- ERP / CRM 数据建模
- RAG 知识增强骨架
- RPA 低风险任务草案
- Human-in-the-loop 风控
- Evals 评测意识
- 前端 Demo 展示能力
