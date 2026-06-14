"""Generate Markdown and JSON reports for the mock workflow demo."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

ROOT_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT_DIR / "outputs"


def write_json(filename: str, data: object) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_markdown_report(
    product_diagnosis: List[Dict[str, object]],
    customer_segments: List[Dict[str, object]],
    rpa_tasks: List[Dict[str, object]],
    rag_context: Dict[str, object],
) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "demo_report.md"

    lines: List[str] = [
        "# AI + RPA + ERP + CRM Mock Workflow Demo Report",
        "",
        "## 1. 商品经营诊断",
    ]

    for item in product_diagnosis:
        lines.extend(
            [
                f"### {item['product_id']} - {item['product_name']}",
                f"- 风险等级：{item['risk_level']}",
                f"- 订单数：{item['order_count']}，库存：{item['stock']}，退款数：{item['refund_count']}",
                f"- 毛利：{item['gross_margin']}，活动毛利：{item['activity_margin']}",
                f"- 风险标签：{', '.join(item['risks']) if item['risks'] else '暂无'}",
                f"- 建议动作：{'；'.join(item['suggested_actions'])}",
                "",
            ]
        )

    lines.append("## 2. CRM 客户分层")
    for item in customer_segments:
        lines.extend(
            [
                f"### {item['customer_id']} - {item['segment']}",
                f"- RFM：{item['rfm_score']}",
                f"- 标签：{', '.join(item['tags'])}",
                f"- 风险等级：{item['risk_level']}",
                f"- 分层依据：{'；'.join(item['basis'])}",
                f"- 建议动作：{'；'.join(item['recommended_actions'])}",
                f"- 是否需要人工确认：{item['requires_human_approval']}",
                "",
            ]
        )

    lines.append("## 3. RPA 任务草案")
    for task in rpa_tasks:
        lines.extend(
            [
                f"### {task['task_id']} - {task['task_type']}",
                f"- 风险等级：{task['risk_level']}",
                f"- 审批状态：{task['approval_status']}",
                f"- 是否允许自动执行：{task['auto_execution_allowed']}",
                f"- 建议：{task['ai_suggestion']}",
                f"- 策略原因：{task['policy_reason']}",
                "",
            ]
        )

    lines.extend(
        [
            "## 4. RAG 召回摘要",
            "",
            "```json",
            json.dumps(rag_context, ensure_ascii=False, indent=2),
            "```",
            "",
            "## 5. 复盘结论",
            "",
            "当前 Demo 已跑通：Mock ERP / CRM 数据导入 → 规则诊断 → 简单 RAG 召回 → RPA 任务草案 → 人工确认边界 → 报告输出。",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
