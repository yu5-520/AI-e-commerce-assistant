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
    category_context: Dict[str, object] | None = None,
    competitor_analysis: Dict[str, object] | None = None,
    listing_growth_plan: Dict[str, object] | None = None,
) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "demo_report.md"
    category_context = category_context or {}
    competitor_analysis = competitor_analysis or {}
    listing_growth_plan = listing_growth_plan or {}
    category_profile = category_context.get("category_profile") or {}
    category_rules = category_context.get("category_rules") or {}
    reference_product = competitor_analysis.get("reference_product") or {}
    price_gap = competitor_analysis.get("price_gap") or {}
    review_gap = competitor_analysis.get("review_gap") or {}
    top_candidate = listing_growth_plan.get("top_candidate") or {}
    listing_draft = listing_growth_plan.get("listing_draft") or {}

    lines: List[str] = [
        "# AI 垂直货架电商经营循环 Demo Report",
        "",
        "## 0. 垂直类目上下文",
        f"- 类目：{category_profile.get('category_name', '未加载')}",
        f"- 来源：{category_profile.get('source', '未加载')}",
        f"- 类目摘要：{category_profile.get('summary', '未加载')}",
        f"- 安全策略：{category_rules.get('safe_output_policy', '未加载')}",
        f"- 集成状态：{category_context.get('integration_status', '未加载')}",
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

    lines.append("## 2. 同类目竞品比对")
    lines.extend(
        [
            f"- 分析 ID：{competitor_analysis.get('analysis_id', '未生成')}",
            f"- 数据来源：{competitor_analysis.get('data_source', '未加载')}",
            f"- 竞品数量：{competitor_analysis.get('competitor_count', 0)}",
            f"- 触发商品：{reference_product.get('product_id', '未选择')}｜{reference_product.get('product_name', '未选择')}",
            f"- 触发原因：{reference_product.get('trigger_reason', '未生成')}",
            f"- 价格带位置：{price_gap.get('position', 'unknown')}｜{price_gap.get('insight', '未生成')}",
            f"- 差评机会：{'、'.join(review_gap.get('top_bad_review_keywords', [])) or '暂无'}",
            f"- 下一步动作：{competitor_analysis.get('next_action', '未生成')}",
            f"- 安全边界：{competitor_analysis.get('safe_use_policy', '未生成')}",
            "",
        ]
    )

    lines.append("## 3. 同类目上新增长")
    lines.extend(
        [
            f"- 计划 ID：{listing_growth_plan.get('plan_id', '未生成')}",
            f"- 数据来源：{listing_growth_plan.get('data_source', '未加载')}",
            f"- 候选商品数：{listing_growth_plan.get('candidate_count', 0)}",
            f"- Top 候选：{top_candidate.get('supplier_product_id', '未选择')}｜{top_candidate.get('product_name', '未选择')}｜评分：{top_candidate.get('score', 'NA')}",
            f"- 预估毛利：{top_candidate.get('expected_margin', 'NA')}｜毛利率：{top_candidate.get('margin_rate', 'NA')}",
            f"- 候选理由：{'；'.join(top_candidate.get('reasons', [])) or '未生成'}",
            f"- 候选风险：{'；'.join(top_candidate.get('risks', [])) or '未生成'}",
            f"- 标题草案：{listing_draft.get('title_draft', '未生成')}",
            f"- 下一步动作：{listing_growth_plan.get('next_action', '未生成')}",
            f"- 安全边界：{listing_growth_plan.get('safe_use_policy', '未生成')}",
            "",
        ]
    )

    lines.append("## 4. CRM 客户分层")
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

    lines.append("## 5. RPA 任务草案")
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
            "## 6. RAG 召回摘要",
            "",
            "```json",
            json.dumps(rag_context, ensure_ascii=False, indent=2),
            "```",
            "",
            "## 7. 类目下一步",
        ]
    )
    for step in category_context.get("next_steps", []):
        lines.append(f"- {step}")

    lines.extend(
        [
            "",
            "## 8. 复盘结论",
            "",
            "当前 Demo 已跑通：Mock ERP / CRM 数据导入 → 垂直类目上下文加载 → 商品经营判断 → 同类目竞品比对 → 同类目上新增长草案 → 简单 RAG 召回 → RPA 任务草案 → 人工确认边界 → 报告输出。",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
