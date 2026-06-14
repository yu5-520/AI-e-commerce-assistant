"""Run the mock ERP + CRM + RAG + RPA workflow demo.

Usage:
    python -m src.run_demo

The demo uses transparent rule-based logic to simulate AI decision nodes. This
keeps the MVP deterministic and easy to inspect; later, each rule node can be
replaced by LLM + RAG calls while preserving the same output contracts.
"""

from __future__ import annotations

from src.data_loader.load_mock_data import load_all
from src.diagnosis.product_diagnosis import diagnose_products
from src.diagnosis.customer_segmentation import segment_customers
from src.rag.simple_retriever import retrieve
from src.rpa_tasks.generate_task_draft import generate_customer_tasks, generate_product_tasks
from src.reports.generate_demo_report import write_json, write_markdown_report


def main() -> None:
    datasets = load_all()

    product_diagnosis = diagnose_products(
        products=datasets["products"],
        orders=datasets["orders"],
        inventory=datasets["inventory"],
        refunds=datasets["refunds"],
    )

    customer_segments = segment_customers(
        customers=datasets["customers"],
        customer_tags=datasets["customer_tags"],
        interactions=datasets["interactions"],
    )

    rag_context = {
        "activity_price": retrieve("活动价 保本线 利润 风险", top_k=3),
        "after_sales": retrieve("退款 售后 客服 SOP 敏感客户", top_k=3),
        "customer_touch": retrieve("客户触达 隐私 自动群发 合规", top_k=3),
    }

    rpa_tasks = generate_product_tasks(product_diagnosis) + generate_customer_tasks(customer_segments)

    write_json("product_diagnosis.json", product_diagnosis)
    write_json("customer_segmentation.json", customer_segments)
    write_json("rpa_task_draft.json", rpa_tasks)
    write_json("rag_retrieval_context.json", rag_context)
    report_path = write_markdown_report(product_diagnosis, customer_segments, rpa_tasks, rag_context)

    print("Mock workflow completed.")
    print(f"Product diagnosis count: {len(product_diagnosis)}")
    print(f"Customer segmentation count: {len(customer_segments)}")
    print(f"RPA task draft count: {len(rpa_tasks)}")
    print(f"Report generated: {report_path}")


if __name__ == "__main__":
    main()
