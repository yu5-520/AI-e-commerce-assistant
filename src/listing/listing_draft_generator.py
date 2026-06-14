from __future__ import annotations

from typing import Dict, List


def _first_items(items: List[str], limit: int = 3) -> List[str]:
    return [item for item in items if item][:limit]


def generate_listing_draft(
    candidate: Dict[str, object],
    category_context: Dict[str, object],
    competitor_analysis: Dict[str, object],
) -> Dict[str, object]:
    """Generate a safe listing material draft for one candidate.

    This is a draft only. It does not publish products, update platform fields,
    or generate any bypass strategy.
    """
    category_profile = category_context.get("category_profile") or {}
    product_name = str(candidate.get("product_name") or "候选商品")
    matched_points = _first_items(candidate.get("matched_selling_points") or [], 3)
    review_actions = _first_items(
        competitor_analysis.get("review_gap", {}).get("opportunity_actions", []),
        3,
    )
    price_gap = competitor_analysis.get("price_gap") or {}

    title_keywords = matched_points or _first_items(category_profile.get("selling_points") or [], 3)
    title_draft = f"{product_name} {' '.join(title_keywords)} 夏季通勤户外外套"

    image_plan = [
        "第一屏突出核心卖点和使用场景，不使用未授权品牌或平台官方背书元素。",
        "补充面料、厚薄、透气、尺码等真实信息，避免绝对化功效承诺。",
        "根据竞品差评机会补充尺码表、实拍色差说明或物流承诺。",
    ]

    sku_plan = [
        "先保留 3-5 个主推颜色，避免一次性铺过多库存。",
        "尺码默认覆盖 M-2XL，若历史尺码咨询多，再扩展 3XL。",
        "设置基础款和升级款差异，避免所有 SKU 只靠低价竞争。",
    ]

    pricing_plan = {
        "reference_position": price_gap.get("position", "unknown"),
        "suggestion": price_gap.get("insight", "先参考同类目价格带，再做小流量测试。"),
        "manual_review_required": True,
    }

    compliance_checklist = [
        "不使用绝对防晒、100% 阻隔、医疗级等无依据功效表达。",
        "不复制竞品标题、主图、详情页或品牌素材。",
        "上架前人工复核成本、库存、发货周期、尺码表和售后承诺。",
        "真实上架、改价、报名活动和投放必须人工确认。",
    ]

    return {
        "draft_id": f"LISTING_{candidate.get('supplier_product_id')}",
        "supplier_product_id": candidate.get("supplier_product_id"),
        "product_name": product_name,
        "category_name": category_profile.get("category_name", "防晒服"),
        "title_draft": title_draft,
        "image_plan": image_plan,
        "sku_plan": sku_plan,
        "pricing_plan": pricing_plan,
        "review_gap_actions": review_actions,
        "compliance_checklist": compliance_checklist,
        "requires_human_approval": True,
        "auto_publish_allowed": False,
        "policy_reason": "上新资料只能作为草案；真实上架、改价、投放和活动报名必须人工确认。",
    }
