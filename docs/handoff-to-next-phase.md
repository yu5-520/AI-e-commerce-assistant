# Handoff to Next Phase

## 当前阶段已完成

V6 前端三段式 Demo 已完成。

## 下一阶段目标

V7 API 可交互 Demo。

## 下一阶段第一步

新增 FastAPI 后端：

```text
src/api/__init__.py
src/api/main.py
requirements.txt
```

## 需要复用的函数

- `src.data_loader.load_mock_data.load_all`
- `src.diagnosis.product_diagnosis.diagnose_products`
- `src.diagnosis.customer_segmentation.segment_customers`
- `src.rag.simple_retriever.retrieve`
- `src.rpa_tasks.generate_task_draft.generate_product_tasks`
- `src.rpa_tasks.generate_task_draft.generate_customer_tasks`

## 推荐接口

```text
GET /api/health
GET /api/demo/run
GET /api/evals/run
```

## 注意

不要接真实 ERP / CRM，不要自动执行高风险动作。
