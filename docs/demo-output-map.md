# Demo 输出文件映射

## Python Workflow 输出

运行：

```bash
python -m src.run_demo
```

生成：

| 文件 | 含义 |
|---|---|
| outputs/product_diagnosis.json | 商品经营诊断结果 |
| outputs/customer_segmentation.json | CRM 客户分层结果 |
| outputs/rpa_task_draft.json | RPA 任务草案 |
| outputs/rag_retrieval_context.json | RAG 召回上下文 |
| outputs/demo_report.md | Markdown 复盘报告 |

## 前端样例输出

位置：

```text
web_demo/sample-output/
```

包含：

| 文件 | 含义 |
|---|---|
| product_diagnosis.sample.json | 商品诊断样例 |
| customer_segmentation.sample.json | 客户分层样例 |
| rpa_task_draft.sample.json | RPA 任务草案样例 |
| rag_retrieval_context.sample.json | RAG 召回样例 |
| approval_required_tasks.sample.json | 人工确认任务样例 |
| eval_results.sample.json | Evals 结果样例 |
| demo_report.sample.md | 复盘报告样例 |

## 映射关系

```text
outputs/*.json
↓
未来 API 返回
↓
web_demo 渲染
```

当前前端使用内置 Mock 数据和 sample-output 作为展示参考，下一阶段将改成直接消费 API 返回结果。
