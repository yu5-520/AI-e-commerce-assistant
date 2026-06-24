"""V10.12 metric and trend evidence engine.

This service makes task generation evidence-first: precise calculated metrics,
metric-baseline RAG, trend comparison, sample confidence, cross validation, and
risk/growth task classification must exist before an Agent draft is trusted.
"""

from __future__ import annotations

from copy import deepcopy
from statistics import mean
from typing import Any, Dict, Iterable, List, Tuple

V1012_METRIC_TREND_EVIDENCE_VERSION = "10.12.0"

RATIO_METRICS = {"ctr", "conversion_rate", "refund_rate", "gross_margin"}
NEGATIVE_METRICS = {"refund_rate", "bad_review_rate", "refund_count", "refund_amount"}
POSITIVE_METRICS = {"roi", "ctr", "conversion_rate", "gross_margin", "orders", "revenue", "sales_volume"}

METRIC_LABELS = {
    "roi": "ROI",
    "ctr": "点击率",
    "conversion_rate": "转化率",
    "refund_rate": "退款率",
    "gross_margin": "毛利率",
    "inventory_sellable_days": "库存可售天数",
    "orders": "订单数",
    "revenue": "成交金额",
    "ad_spend": "广告花费",
    "clicks": "点击量",
    "impressions": "曝光量",
    "refund_count": "退款订单数",
    "stock": "当前库存",
}

# Demo/MVP metric baseline RAG. In production these cards should be stored in the
# vector/indexed RAG layer and resolved by category/platform/stage metadata.
METRIC_BASELINE_RAG: List[Dict[str, Any]] = [
    {
        "baselineId": "MBR-home_living-taobao-stable-roi",
        "metricType": "roi",
        "categoryId": "home_living_goods",
        "platform": "淘宝",
        "productStage": "stable",
        "baselineValue": 1.8,
        "warningBelow": 1.3,
        "dangerBelow": 1.0,
        "excellentAbove": 2.2,
        "sampleRule": {"minClicks": 300, "minOrders": 20},
        "confidence": 0.72,
        "source": "demo_metric_baseline_rag",
    },
    {
        "baselineId": "MBR-home_living-general-roi",
        "metricType": "roi",
        "categoryId": "home_living_goods",
        "platform": "通用",
        "productStage": "stable",
        "baselineValue": 1.6,
        "warningBelow": 1.2,
        "dangerBelow": 0.95,
        "excellentAbove": 2.0,
        "sampleRule": {"minClicks": 200, "minOrders": 15},
        "confidence": 0.68,
        "source": "demo_metric_baseline_rag",
    },
    {
        "baselineId": "MBR-home_living-general-ctr",
        "metricType": "ctr",
        "categoryId": "home_living_goods",
        "platform": "通用",
        "productStage": "stable",
        "baselineValue": 0.035,
        "warningBelow": 0.025,
        "dangerBelow": 0.018,
        "excellentAbove": 0.05,
        "sampleRule": {"minImpressions": 5000, "minClicks": 150},
        "confidence": 0.7,
        "source": "demo_metric_baseline_rag",
    },
    {
        "baselineId": "MBR-home_living-general-cvr",
        "metricType": "conversion_rate",
        "categoryId": "home_living_goods",
        "platform": "通用",
        "productStage": "stable",
        "baselineValue": 0.025,
        "warningBelow": 0.018,
        "dangerBelow": 0.012,
        "excellentAbove": 0.035,
        "sampleRule": {"minClicks": 200, "minOrders": 10},
        "confidence": 0.7,
        "source": "demo_metric_baseline_rag",
    },
    {
        "baselineId": "MBR-home_living-general-refund",
        "metricType": "refund_rate",
        "categoryId": "home_living_goods",
        "platform": "通用",
        "productStage": "stable",
        "baselineValue": 0.04,
        "warningAbove": 0.06,
        "dangerAbove": 0.08,
        "excellentBelow": 0.025,
        "sampleRule": {"minOrders": 20},
        "confidence": 0.73,
        "source": "demo_metric_baseline_rag",
    },
    {
        "baselineId": "MBR-home_living-general-margin",
        "metricType": "gross_margin",
        "categoryId": "home_living_goods",
        "platform": "通用",
        "productStage": "stable",
        "baselineValue": 0.3,
        "warningBelow": 0.25,
        "dangerBelow": 0.18,
        "excellentAbove": 0.42,
        "sampleRule": {"minOrders": 5},
        "confidence": 0.65,
        "source": "demo_metric_baseline_rag",
    },
    {
        "baselineId": "MBR-home_living-general-stock-days",
        "metricType": "inventory_sellable_days",
        "categoryId": "home_living_goods",
        "platform": "通用",
        "productStage": "stable",
        "baselineValue": 14,
        "warningBelow": 7,
        "dangerBelow": 3,
        "excellentAbove": 21,
        "sampleRule": {"minSales7d": 3},
        "confidence": 0.66,
        "source": "demo_metric_baseline_rag",
    },
]


def _pick(mapping: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value not in {None, "", []}:
            return value
    return None


def _as_float(value: Any, default: float | None = None) -> float | None:
    if value in {None, ""}:
        return default
    text = str(value).replace(",", "").replace("¥", "").strip()
    is_percent = text.endswith("%")
    text = text.replace("%", "")
    try:
        number = float(text)
    except (TypeError, ValueError):
        return default
    return number / 100 if is_percent else number


def _normalize_ratio(metric: str, value: float | None) -> float | None:
    if value is None:
        return None
    if metric in RATIO_METRICS and value > 1:
        return value / 100
    return value


def _fmt(metric: str, value: float | None) -> str:
    if value is None:
        return "缺失"
    if metric in RATIO_METRICS:
        return f"{value * 100:.2f}%"
    if metric == "inventory_sellable_days":
        return f"{value:.1f} 天"
    if metric in {"orders", "clicks", "impressions", "refund_count", "stock"}:
        return f"{value:.0f}"
    return f"{value:.2f}"


def _metric_value(raw: Dict[str, Any], metric: str) -> Tuple[float | None, Dict[str, Any]]:
    if metric == "roi":
        explicit = _normalize_ratio("roi", _as_float(_pick(raw, "roi", "ROI", "roas", "ROAS")))
        if explicit is not None:
            return explicit, {"formula": "ROI = 成交金额 / 广告花费", "sourceFields": ["roi"], "calculationType": "imported_or_api_metric"}
        revenue = _as_float(_pick(raw, "revenue", "actual_paid", "sales", "salesAmount", "成交金额", "销售额"))
        spend = _as_float(_pick(raw, "ad_spend", "adSpend", "cost", "广告花费", "投放花费"))
        if revenue is not None and spend and spend > 0:
            return revenue / spend, {"formula": "ROI = 成交金额 / 广告花费", "numerator": revenue, "denominator": spend, "sourceFields": ["revenue", "ad_spend"], "calculationType": "deterministic"}
    if metric == "ctr":
        explicit = _normalize_ratio("ctr", _as_float(_pick(raw, "ctr", "CTR", "clickRate", "点击率")))
        if explicit is not None:
            return explicit, {"formula": "CTR = 点击量 / 曝光量", "sourceFields": ["ctr"], "calculationType": "imported_or_api_metric"}
        clicks = _as_float(_pick(raw, "clicks", "click", "点击量"))
        impressions = _as_float(_pick(raw, "impressions", "exposure", "曝光量", "展现量"))
        if clicks is not None and impressions and impressions > 0:
            return clicks / impressions, {"formula": "CTR = 点击量 / 曝光量", "numerator": clicks, "denominator": impressions, "sourceFields": ["clicks", "impressions"], "calculationType": "deterministic"}
    if metric == "conversion_rate":
        explicit = _normalize_ratio("conversion_rate", _as_float(_pick(raw, "conversion_rate", "conversion", "CVR", "转化率")))
        if explicit is not None:
            return explicit, {"formula": "CVR = 成交订单数 / 点击量", "sourceFields": ["conversion_rate"], "calculationType": "imported_or_api_metric"}
        orders = _as_float(_pick(raw, "orders", "order_count", "成交订单数", "订单数"))
        clicks = _as_float(_pick(raw, "clicks", "click", "点击量"))
        if orders is not None and clicks and clicks > 0:
            return orders / clicks, {"formula": "CVR = 成交订单数 / 点击量", "numerator": orders, "denominator": clicks, "sourceFields": ["orders", "clicks"], "calculationType": "deterministic"}
    if metric == "refund_rate":
        explicit = _normalize_ratio("refund_rate", _as_float(_pick(raw, "refund_rate", "refundRate", "退款率")))
        if explicit is not None:
            return explicit, {"formula": "退款率 = 退款订单数 / 成交订单数", "sourceFields": ["refund_rate"], "calculationType": "imported_or_api_metric"}
        refunds = _as_float(_pick(raw, "refund_count", "refundCount", "退款订单数", "退款数"))
        orders = _as_float(_pick(raw, "orders", "order_count", "成交订单数", "订单数"))
        if refunds is not None and orders and orders > 0:
            return refunds / orders, {"formula": "退款率 = 退款订单数 / 成交订单数", "numerator": refunds, "denominator": orders, "sourceFields": ["refund_count", "orders"], "calculationType": "deterministic"}
    if metric == "gross_margin":
        explicit = _normalize_ratio("gross_margin", _as_float(_pick(raw, "gross_margin", "grossMargin", "毛利率")))
        if explicit is not None:
            return explicit, {"formula": "毛利率 = (成交金额 - 成本) / 成交金额", "sourceFields": ["gross_margin"], "calculationType": "imported_or_api_metric"}
        revenue = _as_float(_pick(raw, "revenue", "actual_paid", "sales", "成交金额", "销售额"))
        cost = _as_float(_pick(raw, "total_cost", "cost", "成本"))
        sale_price = _as_float(_pick(raw, "sale_price", "price", "售价"))
        cost_price = _as_float(_pick(raw, "cost_price", "成本价"))
        quantity = _as_float(_pick(raw, "quantity", "sales_volume", "销量", "订单数"), 1)
        if cost is None and cost_price is not None and quantity is not None:
            cost = cost_price * quantity
        if revenue is None and sale_price is not None and quantity is not None:
            revenue = sale_price * quantity
        if revenue and revenue > 0 and cost is not None:
            return (revenue - cost) / revenue, {"formula": "毛利率 = (成交金额 - 成本) / 成交金额", "numerator": revenue - cost, "denominator": revenue, "sourceFields": ["revenue", "cost"], "calculationType": "deterministic"}
    if metric == "inventory_sellable_days":
        explicit = _as_float(_pick(raw, "inventory_sellable_days", "stockSellableDays", "库存可售天数"))
        if explicit is not None:
            return explicit, {"formula": "库存可售天数 = 当前库存 / 近7日日均销量", "sourceFields": ["inventory_sellable_days"], "calculationType": "imported_or_api_metric"}
        stock = _as_float(_pick(raw, "stock", "available_stock", "库存", "当前库存"))
        avg_daily = _as_float(_pick(raw, "avg_daily_sales_7d", "daily_sales", "近7日日均销量"))
        sales7 = _as_float(_pick(raw, "sales_7d", "seven_day_sales", "近7日销量", "sales_volume", "quantity", "销量"))
        if avg_daily is None and sales7 is not None:
            avg_daily = sales7 / 7
        if stock is not None and avg_daily and avg_daily > 0:
            return stock / avg_daily, {"formula": "库存可售天数 = 当前库存 / 近7日日均销量", "numerator": stock, "denominator": avg_daily, "sourceFields": ["stock", "avg_daily_sales_7d"], "calculationType": "deterministic"}
    value = _as_float(_pick(raw, metric, METRIC_LABELS.get(metric, metric)))
    return value, {"formula": f"{METRIC_LABELS.get(metric, metric)} = 接口/报表字段", "sourceFields": [metric], "calculationType": "imported_or_api_metric"} if value is not None else {}


def calculate_precise_metrics(item: Dict[str, Any], metrics: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    raw = {**(item or {}), **(metrics or {})}
    result: List[Dict[str, Any]] = []
    for metric in ["roi", "ctr", "conversion_rate", "refund_rate", "gross_margin", "inventory_sellable_days", "orders", "revenue", "ad_spend", "clicks", "impressions", "stock"]:
        value, detail = _metric_value(raw, metric)
        if value is None:
            continue
        item_out = {
            "metric": metric,
            "label": METRIC_LABELS.get(metric, metric),
            "value": value,
            "displayValue": _fmt(metric, value),
            "formula": detail.get("formula"),
            "numerator": detail.get("numerator"),
            "denominator": detail.get("denominator"),
            "sourceFields": detail.get("sourceFields") or [metric],
            "calculationType": detail.get("calculationType") or "imported_or_api_metric",
            "precisionRule": "后端确定性计算；AI 不允许编造当前指标数字。",
        }
        result.append(item_out)
    return result


def _baseline_for(metric: str, category_id: str, platform: str, product_stage: str) -> Dict[str, Any] | None:
    candidates = [row for row in METRIC_BASELINE_RAG if row["metricType"] == metric]
    candidates.sort(key=lambda row: (row.get("categoryId") == category_id, row.get("platform") in {platform, "通用"}, row.get("productStage") == product_stage), reverse=True)
    return deepcopy(candidates[0]) if candidates else None


def attach_baselines(metrics: List[Dict[str, Any]], *, category_id: str, platform: str, product_stage: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for metric in metrics:
        item = deepcopy(metric)
        baseline = _baseline_for(metric["metric"], category_id, platform, product_stage)
        if baseline:
            value = item.get("value")
            status = "normal"
            deviation = None
            base_value = baseline.get("baselineValue")
            if base_value not in {None, 0} and value is not None:
                deviation = (value - float(base_value)) / abs(float(base_value))
            if metric["metric"] in NEGATIVE_METRICS:
                if value is not None and baseline.get("dangerAbove") is not None and value >= float(baseline["dangerAbove"]):
                    status = "danger"
                elif value is not None and baseline.get("warningAbove") is not None and value >= float(baseline["warningAbove"]):
                    status = "warning"
                elif value is not None and baseline.get("excellentBelow") is not None and value <= float(baseline["excellentBelow"]):
                    status = "excellent"
            else:
                if value is not None and baseline.get("dangerBelow") is not None and value <= float(baseline["dangerBelow"]):
                    status = "danger"
                elif value is not None and baseline.get("warningBelow") is not None and value <= float(baseline["warningBelow"]):
                    status = "warning"
                elif value is not None and baseline.get("excellentAbove") is not None and value >= float(baseline["excellentAbove"]):
                    status = "excellent"
            item["baseline"] = baseline
            item["baselineStatus"] = status
            item["baselineDeviation"] = round(deviation, 4) if deviation is not None else None
            item["baselineDisplay"] = _fmt(metric["metric"], float(base_value)) if base_value is not None else "缺失"
        else:
            item["baselineStatus"] = "missing_baseline"
        out.append(item)
    return out


def _previous_metrics(raw: Dict[str, Any]) -> Dict[str, Any]:
    prev = raw.get("previousMetrics") or raw.get("previous_metrics") or {}
    if isinstance(prev, dict) and prev:
        return prev
    result: Dict[str, Any] = {}
    for key, value in raw.items():
        if str(key).startswith("previous_"):
            result[str(key).replace("previous_", "")] = value
        if str(key).startswith("prev") and len(str(key)) > 4:
            result[str(key)[4:].lower()] = value
    return result


def trend_compare(current_metrics: List[Dict[str, Any]], raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    prev_raw = _previous_metrics(raw)
    out: List[Dict[str, Any]] = []
    for metric in current_metrics:
        name = metric["metric"]
        current = metric["value"]
        previous, previous_detail = _metric_value(prev_raw, name)
        if previous is None:
            continue
        change = current - previous
        rate = change / abs(previous) if previous not in {0, 0.0} else 0.0
        if abs(rate) < 0.03:
            direction = "stable"
        elif rate > 0:
            direction = "up"
        else:
            direction = "down"
        out.append({
            "metric": name,
            "label": metric["label"],
            "previousValue": previous,
            "currentValue": current,
            "previousDisplay": _fmt(name, previous),
            "currentDisplay": _fmt(name, current),
            "changeValue": change,
            "changeRate": round(rate, 4),
            "changeDisplay": f"{rate * 100:.1f}%",
            "trendDirection": direction,
            "windowType": raw.get("trendWindow") or raw.get("windowType") or "last_snapshot_or_previous_period",
            "formula": f"{metric['label']}趋势 = 当前值 - 对比窗口值",
            "previousCalculationType": previous_detail.get("calculationType"),
        })
    return out


def sample_confidence(metrics: List[Dict[str, Any]], raw: Dict[str, Any]) -> Dict[str, Any]:
    values = {item["metric"]: item["value"] for item in metrics}
    clicks = values.get("clicks") or _as_float(_pick(raw, "clicks", "点击量"), 0) or 0
    orders = values.get("orders") or _as_float(_pick(raw, "orders", "订单数", "成交订单数"), 0) or 0
    impressions = values.get("impressions") or _as_float(_pick(raw, "impressions", "曝光量"), 0) or 0
    score = 0.35
    reasons: List[str] = []
    if clicks >= 300:
        score += 0.25; reasons.append("点击量达到强判断样本")
    elif clicks >= 100:
        score += 0.12; reasons.append("点击量达到观察样本")
    if orders >= 20:
        score += 0.25; reasons.append("订单量达到强判断样本")
    elif orders >= 8:
        score += 0.12; reasons.append("订单量达到观察样本")
    if impressions >= 5000:
        score += 0.1; reasons.append("曝光量达到入口判断样本")
    level = "high" if score >= 0.75 else "medium" if score >= 0.52 else "low"
    if not reasons:
        reasons.append("样本量不足，只能生成观察或补数任务")
    return {"score": round(min(score, 0.95), 2), "level": level, "clicks": clicks, "orders": orders, "impressions": impressions, "reasons": reasons}


def cross_validate(metrics: List[Dict[str, Any]], trends: List[Dict[str, Any]], confidence: Dict[str, Any]) -> Dict[str, Any]:
    by_metric = {item["metric"]: item for item in metrics}
    trend_by_metric = {item["metric"]: item for item in trends}
    findings: List[str] = []
    risk_hits: List[str] = []
    growth_hits: List[str] = []

    roi = by_metric.get("roi")
    ctr = by_metric.get("ctr")
    cvr = by_metric.get("conversion_rate")
    refund = by_metric.get("refund_rate")
    stock_days = by_metric.get("inventory_sellable_days")
    margin = by_metric.get("gross_margin")

    if roi and roi.get("baselineStatus") in {"warning", "danger"}:
        risk_hits.append("ROI 低于基线")
    if roi and trend_by_metric.get("roi", {}).get("trendDirection") == "down":
        risk_hits.append("ROI 趋势下滑")
    if cvr and (cvr.get("baselineStatus") in {"warning", "danger"} or trend_by_metric.get("conversion_rate", {}).get("trendDirection") == "down"):
        risk_hits.append("转化率承接走弱")
    if refund and (refund.get("baselineStatus") in {"warning", "danger"} or trend_by_metric.get("refund_rate", {}).get("trendDirection") == "up"):
        risk_hits.append("退款/售后风险升高")
    if stock_days and stock_days.get("baselineStatus") in {"warning", "danger"}:
        risk_hits.append("库存承接不足")

    if roi and roi.get("baselineStatus") == "excellent" and trend_by_metric.get("roi", {}).get("trendDirection") in {"up", "stable", None}:
        growth_hits.append("ROI 高于优秀线且未走弱")
    if cvr and cvr.get("baselineStatus") == "excellent":
        growth_hits.append("转化率优于基线")
    if ctr and ctr.get("baselineStatus") in {"normal", "excellent"}:
        growth_hits.append("点击入口稳定")
    if refund and refund.get("baselineStatus") in {"normal", "excellent"}:
        growth_hits.append("退款率可承接")
    if stock_days and stock_days.get("baselineStatus") in {"normal", "excellent"}:
        growth_hits.append("库存可承接")
    if margin and margin.get("baselineStatus") in {"normal", "excellent"}:
        growth_hits.append("毛利可承接")

    if "ROI 低于基线" in risk_hits and "转化率承接走弱" in risk_hits and "退款/售后风险升高" in risk_hits:
        findings.append("ROI 低不是单独投流问题，转化和售后同时印证，优先生成承接/售后处理任务。")
    elif "ROI 低于基线" in risk_hits and ctr and ctr.get("baselineStatus") in {"warning", "danger"}:
        findings.append("ROI 低与点击入口偏弱共振，优先生成主图/标题/人群测试任务。")
    elif len(growth_hits) >= 4 and confidence.get("level") in {"medium", "high"}:
        findings.append("增长信号被 ROI、转化、退款、库存或毛利交叉验证，可生成小步放量/主推候选任务。")
    elif risk_hits:
        findings.append("存在风险信号，但需要结合样本量和趋势确认任务强度。")
    else:
        findings.append("未形成强风险或强增长共振，建议观察或补充样本。")

    if confidence.get("level") == "low":
        decision = "observe"
        task_family = "观察/补样本任务"
    elif len(growth_hits) >= 4 and len(risk_hits) <= 1:
        decision = "growth"
        task_family = "增长验证任务"
    elif len(risk_hits) >= 2:
        decision = "risk"
        task_family = "风险处理任务"
    elif len(risk_hits) == 1:
        decision = "observe"
        task_family = "观察复核任务"
    else:
        decision = "review"
        task_family = "数据复核任务"

    return {"decision": decision, "taskFamily": task_family, "riskHits": risk_hits, "growthHits": growth_hits, "findings": findings}


def evidence_summary(metrics: List[Dict[str, Any]], trends: List[Dict[str, Any]], cross: Dict[str, Any]) -> str:
    parts: List[str] = []
    for metric in metrics:
        if metric["metric"] in {"roi", "ctr", "conversion_rate", "refund_rate", "inventory_sellable_days"}:
            baseline = metric.get("baselineDisplay") or "缺失"
            status = metric.get("baselineStatus") or "unknown"
            parts.append(f"{metric['label']}={metric['displayValue']}，基线={baseline}，状态={status}")
    for trend in trends[:4]:
        parts.append(f"{trend['label']}趋势 {trend['previousDisplay']} → {trend['currentDisplay']}，变化 {trend['changeDisplay']}")
    parts.extend(cross.get("findings") or [])
    return "；".join(parts[:8])


def build_metric_trend_evidence(
    item: Dict[str, Any] | None,
    *,
    metrics: Dict[str, Any] | None = None,
    category_id: str | None = None,
    platform: str | None = None,
    product_stage: str | None = None,
) -> Dict[str, Any]:
    raw = {**(item or {}), **(metrics or {})}
    category = category_id or raw.get("categoryId") or raw.get("category") or "home_living_goods"
    platform_value = platform or raw.get("platform") or "通用"
    stage = product_stage or raw.get("productStage") or raw.get("stage") or ("new" if str(raw.get("isNew") or "").lower() in {"1", "true", "yes"} else "stable")
    precise = calculate_precise_metrics(raw, metrics)
    baselined = attach_baselines(precise, category_id=str(category), platform=str(platform_value), product_stage=str(stage))
    trends = trend_compare(baselined, raw)
    confidence = sample_confidence(baselined, raw)
    cross = cross_validate(baselined, trends, confidence)
    return {
        "version": V1012_METRIC_TREND_EVIDENCE_VERSION,
        "evidenceType": "metric_trend_evidence",
        "principle": "精准指标是信任底线；单点只记录，趋势和交叉验证决定任务。权重只作为高级升维层。",
        "categoryId": category,
        "platform": platform_value,
        "productStage": stage,
        "metricEvidence": baselined,
        "trendEvidence": trends,
        "sampleConfidence": confidence,
        "crossValidation": cross,
        "taskDecision": {"decision": cross["decision"], "taskFamily": cross["taskFamily"]},
        "summary": evidence_summary(baselined, trends, cross),
        "baselineRag": {"version": V1012_METRIC_TREND_EVIDENCE_VERSION, "mode": "metric_baseline_rag", "matchedBaselineIds": [item.get("baseline", {}).get("baselineId") for item in baselined if item.get("baseline")], "upgradePath": "正式版可把 metric_baseline 卡写入向量库，并按类目/平台/阶段/店铺历史混合召回。"},
    }
