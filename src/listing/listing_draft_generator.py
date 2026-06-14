from __future__ import annotations

from typing import Dict, List


def _first_items(items: List[str], limit: int = 3) -> List[str]:
    return [item for item in items if item][:limit]


def _scenario_suffix(category_name: str) -> str:
    if "家居" in category_name:
        return "家用多场景实用款"
    if "防晒" in category_name:
        return "夏季户外通勤款"
    if "服饰" in category_name:
        return "日常穿搭基础款"
    return "多场景实用款"


def _image_plan(category_name: str) -> List[str]:
    if "家居" in category_name:
        return [
            "第一屏突出使用场景、功能利益和规格信息，不使用未授权品牌或平台官方背书元素。",
            "补充尺寸、材质、安装方式、承重或使用限制，避免绝对化承诺。",
            "根据竞品差评机会补充尺寸参照、安装说明、实拍色差说明或物流包装承诺。",
        ]
    return [
        "第一屏突出核心卖点和使用场景，不使用未授权品牌或平台官方背书元素。",
        "补充材质、厚薄、透气、尺码等真实信息，避免绝对化功效承诺。",
        "根据竞品差评机会补充尺码表、实拍色差说明或物流承诺。",
    ]


def _sku_plan(category_name: str) -> List[str]:
    if "家居" in category_name:
        return [
            "先保留 2-4 个主推规格或尺寸，避免一次性铺过多库存。",
            "组合款要单独复核物流成本、包装体积和售后理解成本。",
            "基础款和升级款必须有清晰功能差异，避免只靠名称溢价。",
        ]
    return [
        "先保留 3-5 个主推颜色，避免一次性铺过多库存。",
        "尺码默认覆盖主流区间，若历史尺码咨询多，再扩展特殊尺码。",
        "设置基础款和升级款差异，避免所有 SKU 只靠低价竞争。",
    ]


def _compliance_checklist(category_name: str) -> List[str]:
    if "家居" in category_name:
        return [
            "不使用绝对承重、永久耐用、医疗级矫正等无依据表达。",
            "不复制竞品标题、主图、详情页或品牌素材。",
            "上架前人工复核成本、库存、尺寸、材质、安装说明、物流包装和售后承诺。",
            "真实上架、改价、活动报名和投放必须人工确认。",
        ]
    return [
        "不使用绝对防晒、100% 阻隔、医疗级等无依据功效表达。",
        "不复制竞品标题、主图、详情页或品牌素材。",
        "上架前人工复核成本、库存、发货周期、尺码表和售后承诺。",
        "真实上架、改价、活动报名和投放必须人工确认。",
    ]


def generate_listing_draft(
    candidate: Dict[str, object],
    category_context: Dict[str, object],
    competitor_analysis: Dict[str, object],
) -> Dict[str, object]:
    """Generate a safe listing material draft for one candidate.

    This is a draft only. It does not publish products or update platform fields.
    """
    category_profile = category_context.get("category_profile") or {}
    category_name = str(category_profile.get("category_name") or "经营单元")
    product_name = str(candidate.get("product_name") or "候选商品")
    matched_points = _first_items(candidate.get("matched_selling_points") or [], 3)
    review_actions = _first_items(
        competitor_analysis.get("review_gap", {}).get("opportunity_actions", []),
        3,
    )
    price_gap = competitor_analysis.get("price_gap") or {}

    title_keywords = matched_points or _first_items(category_profile.get("selling_points") or [], 3)
    title_draft = f"{product_name} {' '.join(title_keywords)} {_scenario_suffix(category_name)}"

    pricing_plan = {
        "reference_position": price_gap.get("position", "unknown"),
        "suggestion": price_gap.get("insight", "先参考同经营单元价格带，再做小流量测试。"),
        "manual_review_required": True,
    }

    return {
        "draft_id": f"LISTING_{candidate.get('supplier_product_id')}",
        "supplier_product_id": candidate.get("supplier_product_id"),
        "product_name": product_name,
        "category_name": category_name,
        "title_draft": title_draft,
        "image_plan": _image_plan(category_name),
        "sku_plan": _sku_plan(category_name),
        "pricing_plan": pricing_plan,
        "review_gap_actions": review_actions,
        "compliance_checklist": _compliance_checklist(category_name),
        "requires_human_approval": True,
        "auto_publish_allowed": False,
        "policy_reason": "上新资料只能作为草案；真实上架、改价、投放和活动报名必须人工确认。",
    }
