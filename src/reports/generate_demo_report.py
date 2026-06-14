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
    traffic_feedback_report: Dict[str, object] | None = None,
    operating_loop_summary: Dict[str, object] | None = None,
    operating_unit: Dict[str, object] | None = None,
    cycle_policy: Dict[str, object] | None = None,
) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "demo_report.md"
    category_context = category_context or {}
    competitor_analysis = competitor_analysis or {}
    listing_growth_plan = listing_growth_plan or {}
    traffic_feedback_report = traffic_feedback_report or {}
    operating_loop_summary = operating_loop_summary or {}
    operating_unit = operating_unit or category_context.get("operating_unit") or {}
    cycle_policy = cycle_policy or {}
    category_profile = category_context.get("category_profile") or {}
    category_rules = category_context.get("category_rules") or {}
    reference_product = competitor_analysis.get("reference_product") or {}
    price_gap = competitor_analysis.get("price_gap") or {}
    review_gap = competitor_analysis.get("review_gap") or {}
    top_candidate = listing_growth_plan.get("top_candidate") or {}
    listing_draft = listing_growth_plan.get("listing_draft") or {}
    decision_summary = traffic_feedback_report.get("decision_summary") or {}
    risk_summary = traffic_feedback_report.get("risk_summary") or {}

    lines: List[str] = [
        "# AI ERP经营单元电商循环 Demo Report",
        "",
        "## 0. ERP 经营单元识别",
        f"- 经营单元：{operating_unit.get('unit_name', '未推断')}",
        f"- 推断来源：{operating_unit.get('base_source', '未加载')}",
        f"- 商品群：{operating_unit.get('dominant_product_group', '未推断')}",
        f"- 经营单元 ID：{operating_unit.get('operating_unit_id', '未推断')}",
        f"- 推断理由：{operating_unit.get('reason', '未生成')}",
        "",
        "## 0.1 循环频率策略",
        f"- 频率：{cycle_policy.get('cycle_frequency', '未生成')}",
        f"- 循环类型：{cycle_policy.get('cycle_type', '未生成')}",
        f"- 运行时间：{cycle_policy.get('run_time', '未生成')}",
        f"- 报告类型：{cycle_policy.get('report_type', '未生成')}",
        f"- 说明：{cycle_policy.get('description', '未生成')}",
        "",
        "## 0.2 类目 / 经营单元上下文",
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

    lines.append("## 2. 同经营单元竞品比对")
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

    lines.append("## 3. 同经营单元上新增长")
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

    lines.append("## 4. 流量测试与数据回流")
    lines.extend(
        [
            f"- 报告 ID：{traffic_feedback_report.get('report_id', '未生成')}",
            f"- 数据来源：{traffic_feedback_report.get('data_source', '未加载')}",
            f"- 测试实验数：{traffic_feedback_report.get('experiment_count', 0)}",
            f"- 决策分布：{json.dumps(decision_summary, ensure_ascii=False)}",
            f"- 风险分布：{json.dumps(risk_summary, ensure_ascii=False)}",
            f"- 下一步动作：{traffic_feedback_report.get('next_action', '未生成')}",
            f"- 安全边界：{traffic_feedback_report.get('safe_use_policy', '未生成')}",
            "",
            "### 回流动作",
        ]
    )
    for action in traffic_feedback_report.get("loopback_actions", []):
        lines.append(f"- {action}")
    lines.append("")

    lines.append("## 5. 经营循环总控")
    lines.extend(
        [
            f"- 循环 ID：{operating_loop_summary.get('loop_id', '未生成')}",
            f"- 循环状态：{operating_loop_summary.get('loop_status', '未生成')}",
            f"- 下一轮进入模块：{operating_loop_summary.get('next_module', '未生成')}",
            f"- 是否需要人工确认：{operating_loop_summary.get('manual_review_required', True)}",
            f"- 是否允许自动执行：{operating_loop_summary.get('auto_execution_allowed', False)}",
            f"- 安全边界：{operating_loop_summary.get('safe_use_policy', '未生成')}",
            "",
            "### 下一轮计划",
        ]
    )
    for action in operating_loop_summary.get("next_iteration_plan", []):
        lines.append(f"- {action}")
    lines.append("")

    lines.append("## 6. CRM 客户分层")
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

    lines.append("## 7. RPA 任务草案")
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
            "## 8. RAG 召回摘要",
            "",
            "```json",
            json.dumps(rag_context, ensure_ascii=False, indent=2),
            "```",
            "",
            "## 9. 类目下一步",
        ]
    )
    for step in category_context.get("next_steps", []):
        lines.append(f"- {step}")

    lines.extend(
        [
            "",
            "## 10. 复盘结论",
            "",
            "当前 Demo 已跑通：Mock ERP / CRM 数据导入 → ERP 经营单元识别 → 循环频率策略 → 类目上下文加载 → 商品经营判断 → 同经营单元竞品比对 → 同经营单元上新增长草案 → 流量测试回流 → 经营循环总控 → RAG 召回 → RPA 任务草案 → 人工确认边界 → 报告输出。",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
