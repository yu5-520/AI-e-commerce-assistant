from __future__ import annotations

from typing import Dict, List

from src.competitor.competitor_loader import load_mock_competitors
from src.competitor.price_compare import compare_price_band
from src.competitor.review_gap_analysis import analyze_review_gaps
from src.competitor.sku_compare import summarize_sku_gap


def _pick_reference_product(product_diagnosis: List[Dict[str, object]]) -> Dict[str, object]:
    """Pick the most useful product to compare.

    For the MVP, prioritize products with higher risk because competitor analysis
    should be triggered by concrete operating problems, not by random curiosity.
    """
    risk_order = {"high": 3, "medium": 2, "low": 1}
    return sorted(
        product_diagnosis,
        key=lambda item: (risk_order.get(str(item.get("risk_level")), 0), int(item.get("stock") or 0)),
        reverse=True,
    )[0]


def _infer_trigger_reason(product: Dict[str, object]) -> str:
    risks = set(product.get("risks") or [])
    if "refund_abnormal_risk" in risks:
        return "退款异常，优先比对竞品差评、卖点承诺和售后问题。"
    if "high_inventory_low_order_risk" in risks:
        return "高库存低订单，优先比对竞品价格带、主图卖点和 SKU 结构。"
    if "activity_price_margin_risk" in risks:
        return "活动价存在利润风险，优先比对竞品活动价与价格带位置。"
    return "基础经营风险较低，可用同类目竞品比对寻找优化和扩品机会。"


def _suggest_next_action(price_gap: Dict[str, object], review_gap: Dict[str, object]) -> str:
    position = price_gap.get("position")
    review_keywords = " ".join(str(item) for item in review_gap.get("top_bad_review_keywords", []))
    if position == "below_market":
        return "先复核利润安全线和品质预期，再决定是否低价清货或保守测试。"
    if position == "above_market":
        return "先强化主图卖点、材质说明和评价承接，不建议直接放量。"
    if "尺码" in review_keywords or "袖长" in review_keywords:
        return "优先优化尺码表、SKU 说明和客服引导，再进入流量测试。"
    return "可进入标题 / 主图 / SKU 小流量测试，并把测试结果回流经营判断。"


def build_competitor_analysis(
    product_diagnosis: List[Dict[str, object]],
    category_context: Dict[str, object],
) -> Dict[str, object]:
    """Build same-category competitor analysis from mock competitor data."""
    competitors = load_mock_competitors()
    reference_product = _pick_reference_product(product_diagnosis)
    price_gap = compare_price_band(reference_product, competitors)
    sku_gap = summarize_sku_gap(competitors)
    review_gap = analyze_review_gaps(competitors)
    category_profile = category_context.get("category_profile") or {}

    return {
        "analysis_id": "COMP_SUN_PROTECTION_001",
        "category_id": category_profile.get("category_id", "sun_protection_clothing"),
        "category_name": category_profile.get("category_name", "防晒服"),
        "data_source": "examples/category_sun_protection/mock_competitors.csv",
        "mvp_boundary": "Mock / manually prepared competitor rows only; no real platform crawling or automated scraping.",
        "reference_product": {
            "product_id": reference_product.get("product_id"),
            "product_name": reference_product.get("product_name"),
            "risk_level": reference_product.get("risk_level"),
            "risks": reference_product.get("risks", []),
            "trigger_reason": _infer_trigger_reason(reference_product),
        },
        "competitor_count": len(competitors),
        "price_gap": price_gap,
        "sku_gap": sku_gap,
        "review_gap": review_gap,
        "next_action": _suggest_next_action(price_gap, review_gap),
        "safe_use_policy": "只拆解同类目需求结构和差异化机会，不复制竞品标题、图片、详情页或品牌素材。",
    }
