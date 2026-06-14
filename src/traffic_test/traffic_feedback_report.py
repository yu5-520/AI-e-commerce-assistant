from __future__ import annotations

from collections import Counter
from typing import Dict, List

from src.traffic_test.metrics_diagnosis import diagnose_traffic_tests
from src.traffic_test.traffic_loader import load_mock_traffic_tests, traffic_data_source


def build_traffic_feedback_report(
    category_context: Dict[str, object],
    listing_growth_plan: Dict[str, object],
) -> Dict[str, object]:
    """Build traffic test feedback report from mock experiments."""
    category_profile = category_context.get("category_profile") or {}
    category_id = str(category_profile.get("category_id", "home_living_goods"))
    rows = load_mock_traffic_tests(category_id)
    diagnoses = diagnose_traffic_tests(rows)
    decision_counter = Counter(item["decision"] for item in diagnoses)
    risk_counter = Counter(item["risk_level"] for item in diagnoses)
    top_candidate = listing_growth_plan.get("top_candidate") or {}

    high_priority_items = [
        item for item in diagnoses if item["risk_level"] in {"high", "medium"}
    ]

    loopback_actions = _build_loopback_actions(diagnoses)

    return {
        "report_id": f"TRAFFIC_FEEDBACK_{category_id.upper()}_001",
        "category_id": category_id,
        "category_name": category_profile.get("category_name", "家居生活商品"),
        "data_source": traffic_data_source(category_id),
        "mvp_boundary": "Mock / manually prepared traffic rows only; no real ad account or platform campaign operation.",
        "related_listing_candidate": top_candidate.get("supplier_product_id"),
        "experiment_count": len(diagnoses),
        "decision_summary": dict(decision_counter),
        "risk_summary": dict(risk_counter),
        "diagnoses": diagnoses,
        "high_priority_items": high_priority_items,
        "loopback_actions": loopback_actions,
        "next_action": _pick_report_next_action(decision_counter),
        "safe_use_policy": "只生成流量测试复盘和下一步动作建议；真实加预算、改价、换图、上下架必须人工确认。",
    }


def _build_loopback_actions(diagnoses: List[Dict[str, object]]) -> List[str]:
    actions: List[str] = []
    decisions = {item["decision"] for item in diagnoses}
    if "change_title_or_main_image" in decisions:
        actions.append("回流到商品经营判断：标记主图 / 标题点击问题，触发同经营单元竞品主图与标题复查。")
    if "adjust_sku_price_or_detail_page" in decisions:
        actions.append("回流到商品经营判断：标记 SKU / 价格 / 详情页承接问题，进入 SKU 和定价复盘。")
    if "enter_after_sales_diagnosis" in decisions:
        actions.append("回流到 CRM / 售后判断：标记高退款实验，进入尺寸、材质、物流和客服 SOP 归因。")
    if "stop_or_reduce_budget" in decisions:
        actions.append("回流到经营判断：标记 ROI 低，暂停放量并要求人工复核预算策略。")
    if "scale_carefully" in decisions:
        actions.append("回流到经营判断：标记可小幅放量，但必须继续观察退款率、ROI 和库存承接。")
    if not actions:
        actions.append("回流到经营判断：继续收集曝光、点击、转化、退款和 ROI 数据。")
    return actions


def _pick_report_next_action(decision_counter: Counter[str]) -> str:
    if decision_counter.get("enter_after_sales_diagnosis", 0) > 0:
        return "优先处理高退款实验，进入售后归因，再决定是否继续投流。"
    if decision_counter.get("stop_or_reduce_budget", 0) > 0:
        return "存在 ROI 低实验，不建议直接放量，先缩小测试并复核素材、价格和 SKU。"
    if decision_counter.get("change_title_or_main_image", 0) > 0:
        return "优先替换标题或主图第一屏，再做下一轮小流量测试。"
    if decision_counter.get("adjust_sku_price_or_detail_page", 0) > 0:
        return "优先调整 SKU、定价或详情页承接，再继续测试。"
    if decision_counter.get("scale_carefully", 0) > 0:
        return "可小幅放量，但保持人工确认和退款率观察。"
    return "继续测试并沉淀更多数据。"
