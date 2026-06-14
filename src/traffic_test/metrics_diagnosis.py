from __future__ import annotations

from typing import Dict, List

from src.data_loader.load_mock_data import to_int, to_number


def diagnose_traffic_test(row: Dict[str, str]) -> Dict[str, object]:
    """Diagnose one traffic experiment row and suggest the next operating action."""
    impressions = to_int(row.get("impressions"))
    clicks = to_int(row.get("clicks"))
    orders = to_int(row.get("orders"))
    refund_count = to_int(row.get("refund_count"))
    roi = to_number(row.get("roi"))

    click_rate = clicks / max(impressions, 1)
    conversion_rate = orders / max(clicks, 1)
    refund_rate = refund_count / max(orders, 1)

    findings: List[str] = []
    next_actions: List[str] = []
    risk_level = "low"

    if click_rate < 0.025:
        findings.append("click_low")
        next_actions.append("点击率偏低，优先检查标题关键词、主图第一屏和价格带吸引力")
        risk_level = "medium"

    if click_rate >= 0.025 and conversion_rate < 0.04:
        findings.append("conversion_low")
        next_actions.append("点击有承接但转化偏低，优先检查 SKU、详情页、评价和价格承接")
        risk_level = "medium"

    if refund_rate >= 0.1:
        findings.append("refund_high")
        next_actions.append("成交后退款偏高，优先进入尺码、面料、卖点承诺和物流售后归因")
        risk_level = "high" if refund_rate >= 0.15 else "medium"

    if roi < 1:
        findings.append("roi_low")
        next_actions.append("ROI 低于 1，不建议放量，先缩小测试或调整素材与价格")
        risk_level = "high" if risk_level == "high" else "medium"

    if not findings:
        findings.append("test_healthy")
        next_actions.append("测试指标相对健康，可继续观察或小幅扩大测试")

    decision = decide_next_action(findings, roi, refund_rate)

    return {
        "experiment_id": row.get("experiment_id"),
        "product_id": row.get("product_id"),
        "category": row.get("category"),
        "title_version": row.get("title_version"),
        "image_version": row.get("image_version"),
        "sku_version": row.get("sku_version"),
        "test_price": to_number(row.get("test_price")),
        "traffic_source": row.get("traffic_source"),
        "impressions": impressions,
        "clicks": clicks,
        "orders": orders,
        "click_rate": round(click_rate, 4),
        "conversion_rate": round(conversion_rate, 4),
        "refund_rate": round(refund_rate, 4),
        "roi": round(roi, 2),
        "findings": findings,
        "risk_level": risk_level,
        "recommended_actions": next_actions,
        "decision": decision,
    }


def decide_next_action(findings: List[str], roi: float, refund_rate: float) -> str:
    if "refund_high" in findings:
        return "enter_after_sales_diagnosis"
    if "roi_low" in findings:
        return "stop_or_reduce_budget"
    if "click_low" in findings:
        return "change_title_or_main_image"
    if "conversion_low" in findings:
        return "adjust_sku_price_or_detail_page"
    if roi >= 1.5 and refund_rate < 0.08:
        return "scale_carefully"
    return "continue_testing"


def diagnose_traffic_tests(rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    return [diagnose_traffic_test(row) for row in rows]
