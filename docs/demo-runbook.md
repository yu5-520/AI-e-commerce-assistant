# Mock Workflow Demo Runbook

## 1. 目标

本 Runbook 用于说明如何运行当前仓库的最小可运行 AI 工作流 Demo。

当前 Demo 不调用真实大模型，也不接入真实 ERP / CRM API，而是使用规则引擎模拟 AI 诊断节点，使用关键词检索模拟 RAG 节点，使用结构化任务草案模拟 RPA 节点。

这样做的目的：

- 先跑通业务数据链路。
- 先验证输入输出结构。
- 先验证风险边界和人工确认机制。
- 后续再替换为 LLM + RAG + MCP / API 调用。

## 2. 运行方式

在仓库根目录运行：

```bash
python -m src.run_demo
```

运行后会生成：

```text
outputs/product_diagnosis.json
outputs/customer_segmentation.json
outputs/rpa_task_draft.json
outputs/rag_retrieval_context.json
outputs/demo_report.md
```

## 3. 当前链路

```text
读取 examples/ Mock ERP + CRM 数据
↓
商品经营诊断
↓
客户分层分析
↓
关键词 RAG 召回
↓
生成 RPA 任务草案
↓
人工确认边界标记
↓
输出 JSON 与 Markdown 报告
```

## 4. 运行 Evals

```bash
python evals/run_evals.py
```

运行后会生成：

```text
evals/results/latest_results.json
```

当前最小评测包括：

- CRM 是否能识别售后敏感客户。
- RPA 是否禁止生成自动改价、自动群发、自动退款等高风险任务。
- 所有任务是否进入人工确认。

## 5. 当前边界

当前 Demo 不做：

- 自动上架
- 自动改价
- 自动报名活动
- 自动投放广告
- 自动群发客户
- 自动处理退款
- 自动连接真实店铺后台
- 自动连接真实 ERP / CRM

## 6. 后续替换方向

当前规则节点可以逐步替换为：

- LLM 商品诊断节点
- LLM 客户分层节点
- Embedding + 向量库 RAG 检索
- Function Calling / MCP 工具调用
- RPA 执行器
- 前端确认页面

核心原则不变：

> 数据进入系统，AI 做判断，RAG 给依据，人工控风险，RPA 做低风险执行，日志做复盘。
