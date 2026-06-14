from __future__ import annotations

from collections import Counter
from typing import Dict, List


def build_operating_loop_summary(
    category_context: Dict[str, object],
    product_diagnosis: List[Dict[str, object]],
    customer_segmentation: List[Dict[str, object]],
    competitor_analysis: Dict[str, object],
    listing_growth_plan: Dict[str, object],
    traffic_feedback_report: Dict[str, object],
) -> Dict[str, object]:
    """Summarize the full vertical shelf ecommerce operating loop.

    This is the V1.3 control node: it does not replace individual modules; it
    tells the user which module should receive the next iteration.
    """
    category_profile = category_context.get("category_profile") or {}
    product_risks = Counter(item.get("risk_level", "unknown") for item in product_diagnosis)
    customer_risks = Counter(item.get("risk_level", "unknown") for item in customer_segmentation)
    traffic_decisions = traffic_feedback_report.get("decision_summary") or {}
    loopback_actions = traffic_feedback_report.get("loopback_actions") or []

    next_module = _choose_next_module(traffic_decisions, product_risks, customer_risks)
    next_iteration_plan = _build_next_iteration_plan(next_module, loopback_actions)

    return {
        "loop_id": "OPERATING_LOOP_SUN_PROTECTION_001",
        "category_id": category_profile.get("category_id", "sun_protection_clothing"),
        "category_name": category_profile.get("category_name", "防晒服"),
        "loop_status": "closed_loop_mock_ready",
        "completed_nodes": [
            "category_context",
            "product_diagnosis",
            "competitor_analysis",
            "listing_growth_plan",
            "traffic_feedback_report",
            "customer_segmentation",
            "rpa_task_draft",
            "human_approval_boundary",
            "report_output",
        ],
        "current_cycle_summary": {
            "product_count": len(product_diagnosis),
            "customer_count": len(customer_segmentation),
            "product_risk_summary": dict(product_risks),
            "customer_risk_summary": dict(customer_risks),
            "competitor_count": competitor_analysis.get("competitor_count", 0),
            "listing_candidate_count": listing_growth_plan.get("candidate_count", 0),
            "traffic_experiment_count": traffic_feedback_report.get("experiment_count", 0),
            "traffic_decision_summary": traffic_decisions,
        },
        "next_module": next_module,
        "next_iteration_plan": next_iteration_plan,
        "loopback_actions": loopback_actions,
        "manual_review_required": True,
        "auto_execution_allowed": False,
        "safe_use_policy": "完整经营循环只生成诊断、草案、复盘和下一轮动作建议；真实平台写入、投放、改价、上架、群发和退款必须人工确认。",
    }


def _choose_next_module(
    traffic_decisions: Dict[str, int],
    product_risks: Counter[str],
    customer_risks: Counter[str],
) -> str:
    if traffic_decisions.get("enter_after_sales_diagnosis", 0) > 0 or customer_risks.get("high", 0) > 0:
        return "crm_after_sales_diagnosis"
    if traffic_decisions.get("stop_or_reduce_budget", 0) > 0:
        return "erp_profit_and_budget_review"
    if traffic_decisions.get("change_title_or_main_image", 0) > 0:
        return "competitor_title_image_review"
    if traffic_decisions.get("adjust_sku_price_or_detail_page", 0) > 0:
        return "listing_sku_pricing_review"
    if product_risks.get("high", 0) > 0:
        return "erp_product_risk_review"
    if traffic_decisions.get("scale_carefully", 0) > 0:
        return "controlled_scale_review"
    return "continue_operating_loop"


def _build_next_iteration_plan(next_module: str, loopback_actions: List[str]) -> List[str]:
    module_actions = {
        "crm_after_sales_diagnosis": [
            "优先处理高退款和售后敏感问题。",
            "复查尺码、面料、物流、客服 SOP 和卖点承诺。",
            "售后归因完成前，不建议继续放量。",
        ],
        "erp_profit_and_budget_review": [
            "复核活动价、成本、物流费、退款损耗和 ROI。",
            "暂停或缩小低 ROI 流量测试。",
            "人工确认后再决定是否进入下一轮测试。",
        ],
        "competitor_title_image_review": [
            "回到同类目竞品比对，复查标题关键词和主图第一屏卖点。",
            "生成下一版标题 / 主图测试方向。",
            "保持小流量测试，不直接放量。",
        ],
        "listing_sku_pricing_review": [
            "回到上新增长系统，复查 SKU 结构、定价和详情页承接。",
            "生成下一版 SKU / 定价 / 详情页修改草案。",
            "修改前必须人工确认。",
        ],
        "erp_product_risk_review": [
            "回到 ERP 商品经营判断，优先处理高风险商品。",
            "复查库存、退款、毛利和活动价风险。",
            "必要时暂停上新或流量测试。",
        ],
        "controlled_scale_review": [
            "可以小幅放量，但必须继续观察退款率、ROI 和库存承接。",
            "设置下一轮测试阈值和人工确认节点。",
            "放量动作不得自动执行。",
        ],
        "continue_operating_loop": [
            "继续收集经营、竞品、上新和流量测试数据。",
            "保持当前工作流循环。",
            "下一轮根据新数据重新判断触发模块。",
        ],
    }
    actions = module_actions.get(next_module, module_actions["continue_operating_loop"])
    return actions + list(loopback_actions[:3])
