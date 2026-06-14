from __future__ import annotations

from typing import Dict

from src.listing.candidate_scoring import score_supplier_products
from src.listing.listing_draft_generator import generate_listing_draft
from src.listing.supplier_loader import load_mock_supplier_products, supplier_data_source


def build_listing_growth_plan(
    category_context: Dict[str, object],
    competitor_analysis: Dict[str, object],
) -> Dict[str, object]:
    """Build same-operating-unit listing growth plan from mock supplier products."""
    category_profile = category_context.get("category_profile") or {}
    category_id = str(category_profile.get("category_id", "home_living_goods"))
    supplier_products = load_mock_supplier_products(category_id)
    candidates = score_supplier_products(supplier_products, category_context, competitor_analysis)
    top_candidate = candidates[0] if candidates else {}
    listing_draft = (
        generate_listing_draft(top_candidate, category_context, competitor_analysis)
        if top_candidate
        else {}
    )

    return {
        "plan_id": f"LISTING_GROWTH_{category_id.upper()}_001",
        "category_id": category_id,
        "category_name": category_profile.get("category_name", "家居生活商品"),
        "data_source": supplier_data_source(category_id),
        "mvp_boundary": "Mock / manually prepared supplier rows only; no real supplier API or automatic product publishing.",
        "candidate_count": len(candidates),
        "top_candidate": top_candidate,
        "all_candidates": candidates,
        "listing_draft": listing_draft,
        "next_action": "人工复核候选评分、利润安全线、规格说明、主图方向和上新检查表，再进入小流量测试计划。",
        "safe_use_policy": "只生成上新资料草案和测试计划；真实上架、改价、投放和活动报名必须人工确认。",
    }
