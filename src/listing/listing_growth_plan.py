from __future__ import annotations

from typing import Dict

from src.listing.candidate_scoring import score_supplier_products
from src.listing.listing_draft_generator import generate_listing_draft
from src.listing.supplier_loader import load_mock_supplier_products


def build_listing_growth_plan(
    category_context: Dict[str, object],
    competitor_analysis: Dict[str, object],
) -> Dict[str, object]:
    """Build same-category listing growth plan from mock supplier products."""
    supplier_products = load_mock_supplier_products()
    candidates = score_supplier_products(supplier_products, category_context, competitor_analysis)
    top_candidate = candidates[0] if candidates else {}
    listing_draft = (
        generate_listing_draft(top_candidate, category_context, competitor_analysis)
        if top_candidate
        else {}
    )
    category_profile = category_context.get("category_profile") or {}

    return {
        "plan_id": "LISTING_GROWTH_SUN_PROTECTION_001",
        "category_id": category_profile.get("category_id", "sun_protection_clothing"),
        "category_name": category_profile.get("category_name", "防晒服"),
        "data_source": "examples/category_sun_protection/mock_supplier_products.csv",
        "mvp_boundary": "Mock / manually prepared supplier rows only; no real supplier API or automatic product publishing.",
        "candidate_count": len(candidates),
        "top_candidate": top_candidate,
        "all_candidates": candidates,
        "listing_draft": listing_draft,
        "next_action": "人工复核候选评分、利润安全线、尺码表、主图方向和上新检查表，再进入小流量测试计划。",
        "safe_use_policy": "只生成上新资料草案和测试计划；真实上架、改价、投放和活动报名必须人工确认。",
    }
