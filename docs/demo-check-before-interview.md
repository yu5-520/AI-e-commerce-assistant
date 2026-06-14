# 面试前 Demo 检查清单

## 1. 仓库首页

- [ ] README 标题是否清楚
- [ ] 当前定位是否是 AI + RPA + ERP + CRM
- [ ] 是否明确 Workflow-first，不是无边界 Agent
- [ ] 是否能看到运行方式

## 2. Python Workflow

运行：

```bash
python -m src.run_demo
```

检查：

- [ ] 是否生成 outputs/demo_report.md
- [ ] 是否生成 product_diagnosis.json
- [ ] 是否生成 customer_segmentation.json
- [ ] 是否生成 rpa_task_draft.json
- [ ] 是否生成 rag_retrieval_context.json

## 3. Evals

运行：

```bash
python evals/run_evals.py
```

检查：

- [ ] 是否全部 passed
- [ ] 是否生成 evals/results/latest_results.json

## 4. 前端 Demo

打开：

```text
web_demo/index.html
```

检查：

- [ ] 首页是否正常显示
- [ ] 点击导入 Mock 数据是否正常
- [ ] 点击生成 AI 诊断是否正常
- [ ] 点击生成 RPA 任务草案是否正常
- [ ] 点击查看人工确认项是否正常

## 5. 讲解材料

优先准备：

- [ ] docs/one-minute-demo-script.md
- [ ] docs/two-minute-interview-script.md
- [ ] docs/recruiter-project-summary.md
- [ ] docs/resume-project-bullets.md
- [ ] docs/interview-answer-current-limits.md

## 6. 重点提醒

面试时不要说：

- 已经是生产级系统
- 已经接入真实 ERP / CRM
- 已经自动运营店铺
- 已经实现深度 Agent

应该说：

> 当前是可运行 MVP 骨架，已跑通 Mock 数据到诊断、任务草案、人工确认和报告输出的闭环，后续可以替换为真实模型、RAG、API 和 RPA 执行器。
