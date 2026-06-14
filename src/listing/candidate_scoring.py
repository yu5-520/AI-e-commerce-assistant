from __future__ import annotations

from typing import Dict, List

from src.data_loader.load_mock_data import to_int, to_number


def _split_pipe(value: object) -> List[str]:
    return [item.strip() for item in str(value or "").split("|") if item.strip()]


def score_supplier_product(
    supplier_product: Dict[str, str],
    category_context: Dict[str, object],
    competitor_analysis: Dict[str, object],
) -> Dict[str, object]:
    """Score one supplier product as a same-category listing candidate."""
    category_profile = category_context.get("category_profile") or {}
    selling_points = set(category_profile.get("selling_points") or [])
    supplier_points = set(_split_pipe(supplier_product.get("selling_points")))
    matched_points = sorted(selling_points.intersection(supplier_points))

    cost = to_number(supplier_product.get("cost"))
    suggested_price = to_number(supplier_product.get("suggested_price"))
    shipping_cost = to_number(supplier_product.get("shipping_cost"))
    stock = to_int(supplier_product.get("stock"))
    lead_time_days = to_int(supplier_product.get("lead_time_days"))
    expected_margin = suggested_price - cost - shipping_cost
    margin_rate = expected_margin / max(suggested_price, 1)

    score = 50
    reasons: List[str] = []
    risks: List[str] = []

    if supplier_product.get("category") == category_profile.get("category_name"):
        score += 15
        reasons.append("符合当前垂直类目")

    if margin_rate >= 0.35:
        score += 15
        reasons.append("建议售价下仍有较好毛利空间")
    elif margin_rate >= 0.2:
        score += 8
        reasons.append("建议售价下毛利空间可测")
    else:
        score -= 15
        risks.append("毛利空间偏低，上新前需复核成本和活动价")

    if stock >= 200:
        score += 10
        reasons.append("库存承接能力较好")
    else:
        score -= 5
        risks.append("库存较少，不能直接放量")

    if lead_time_days <= 3:
        score += 5
        reasons.append("发货周期可接受")
    else:
        score -= 8
        risks.append("发货周期偏长，需控制承诺")

    if matched_points:
        score += min(len(matched_points) * 3, 12)
        reasons.append(f"匹配类目卖点：{'、'.join(matched_points[:4])}")

    risk_flags = _split_pipe(supplier_product.get("risk_flags"))
    if risk_flags:
        risks.extend([f"供应链风险：{item}" for item in risk_flags])
        score -= min(len(risk_flags) * 3, 9)

    review_keywords = " ".join(competitor_analysis.get("review_gap", {}).get("top_bad_review_keywords", []))
    if "尺码" in review_keywords and "尺码" in " ".join(risk_flags):
        score -= 5
        risks.append("竞品差评与供应链风险都指向尺码问题，需重点做尺码承接")

    score = max(0, min(100, score))
    candidate_level = "high" if score >= 80 else "medium" if score >= 65 else "low"

    return {
        "supplier_product_id": supplier_product.get("supplier_product_id"),
        "product_name": supplier_product.get("product_name"),
        "category": supplier_product.get("category"),
        "score": score,
        "candidate_level": candidate_level,
        "expected_margin": round(expected_margin, 2),
        "margin_rate": round(margin_rate, 4),
        "stock": stock,
        "lead_time_days": lead_time_days,
        "matched_selling_points": matched_points,
        "reasons": reasons,
        "risks": risks or ["暂无明显上新风险，但仍需人工复核"],
    }


def score_supplier_products(
    supplier_products: List[Dict[str, str]],
    category_context: Dict[str, object],
    competitor_analysis: Dict[str, object],
) -> List[Dict[str, object]]:
    candidates = [
        score_supplier_product(row, category_context, competitor_analysis)
        for row in supplier_products
    ]
    return sorted(candidates, key=lambda item: (item["score"], item["expected_margin"]), reverse=True)
