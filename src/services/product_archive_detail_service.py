"""V12.1.2 product archive detail projection.

商品模块只负责商品资产、定位、指标事实和任务历史摘要。完整的任务证据、
交叉验证和 SOP 仍然属于任务详情页。
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.repositories.sqlite_repository import connect, loads
from src.services.metric_fact_store_service import ensure_metric_fact_tables

PRODUCT_ARCHIVE_DETAIL_VERSION = "12.1.2"

METRIC_LABELS = {
    "inventory_qty": "库存数量",
    "sellable_days": "可售天数",
    "avg_order_value": "客单价",
    "sale_price": "售价",
    "payment_amount": "支付金额",
    "product_cost_amount": "商品成本金额",
    "gross_profit_amount": "毛利金额",
    "gross_margin_rate": "毛利率",
    "visitor_count": "访客数",
    "page_view_count": "浏览量",
    "click_user_count": "点击人数",
    "click_count": "点击数",
    "click_rate": "点击率",
    "payment_buyer_count": "支付买家数",
    "payment_order_count": "支付订单数",
    "payment_unit_count": "支付件数",
    "payment_conversion_rate": "支付转化率",
    "refund_order_count": "退款订单数",
    "refund_amount": "退款金额",
    "refund_rate": "退款率",
    "ad_spend": "广告消耗",
    "ad_click_count": "广告点击数",
    "ad_order_count": "广告成交数",
    "roi": "ROI",
    "organic_visitor_count": "自然流量访客数",
    "paid_visitor_count": "付费流量访客数",
}

SECTION_RULES = [
    ("identity", "商品定位", []),
    ("transaction", "成交与投产", ["payment_amount", "avg_order_value", "payment_order_count", "payment_unit_count", "payment_conversion_rate", "roi"]),
    ("profit", "成本与利润", ["product_cost_amount", "gross_profit_amount", "gross_margin_rate"]),
    ("traffic", "流量与广告", ["visitor_count", "page_view_count", "click_user_count", "click_rate", "ad_spend", "ad_click_count", "ad_order_count", "organic_visitor_count", "paid_visitor_count"]),
    ("stock_after_sales", "库存与售后", ["inventory_qty", "sellable_days", "refund_order_count", "refund_amount", "refund_rate"]),
]

TABLES = ("product_metric_facts", "traffic_source_facts", "store_metric_facts")


def _text(value: Any) -> str:
    return str(value or "").strip()


def _item_value(item: Dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = _text(item.get(key))
        if value and value != "—":
            return value
    return ""


def _where_for_table(table: str, item: Dict[str, Any]) -> tuple[str, List[Any]]:
    store_values = [
        _item_value(item, "systemStoreCode"),
        _item_value(item, "storeId", "normalizedStoreId"),
        _item_value(item, "storeName", "store", "normalizedStoreName"),
    ]
    product_values = [
        _item_value(item, "systemSkuCode"),
        _item_value(item, "systemLinkCode"),
        _item_value(item, "systemSpuCode"),
        _item_value(item, "productId", "rawProductId", "id"),
        _item_value(item, "skuId"),
        _item_value(item, "erpProductCode"),
        _item_value(item, "productLink", "link"),
    ]
    store_clauses: List[str] = []
    store_params: List[Any] = []
    for column, value in [("store_code", store_values[0]), ("store_id", store_values[1]), ("store_name", store_values[2])]:
        if value:
            store_clauses.append(f"{column} = ?")
            store_params.append(value)
    if table == "store_metric_facts":
        if not store_clauses:
            return "1 = 0", []
        return " OR ".join(store_clauses), store_params

    product_clauses: List[str] = []
    product_params: List[Any] = []
    for column, value in [
        ("sku_code", product_values[0]),
        ("link_code", product_values[1]),
        ("spu_code", product_values[2]),
        ("product_id", product_values[3]),
        ("sku_id", product_values[4]),
        ("erp_product_code", product_values[5]),
        ("product_link", product_values[6]),
    ]:
        if value:
            product_clauses.append(f"{column} = ?")
            product_params.append(value)
    if not product_clauses:
        return "1 = 0", []
    if store_clauses:
        return f"({' OR '.join(product_clauses)}) AND ({' OR '.join(store_clauses)})", [*product_params, *store_params]
    return " OR ".join(product_clauses), product_params


def _fetch_facts(item: Dict[str, Any], limit: int = 500) -> List[Dict[str, Any]]:
    ensure_metric_fact_tables()
    facts: List[Dict[str, Any]] = []
    with connect() as conn:
        for table in TABLES:
            where, params = _where_for_table(table, item)
            rows = conn.execute(
                f"""
                SELECT *, ? AS fact_table
                FROM {table}
                WHERE {where}
                ORDER BY COALESCE(stat_date, updated_at) DESC, updated_at DESC
                LIMIT ?
                """,
                [table, *params, limit],
            ).fetchall()
            for row in rows:
                payload = loads(row["payload"])
                facts.append({
                    "factId": row["fact_id"],
                    "factTable": row["fact_table"],
                    "entityLevel": row["entity_level"],
                    "metricCode": row["metric_code"],
                    "metricName": METRIC_LABELS.get(row["metric_code"], row["metric_code"]),
                    "metricValue": row["metric_value"],
                    "displayValue": row["display_value"] or str(row["metric_value"] or "—"),
                    "rawFieldName": row["raw_field_name"],
                    "rawValue": row["raw_value"],
                    "sourceSheet": row["source_sheet"],
                    "sourceSystem": row["source_system"],
                    "sourceReportId": row["source_report_id"],
                    "dataVersion": row["data_version"],
                    "datasetName": row["dataset_name"],
                    "statDate": row["stat_date"],
                    "trafficSource": row["traffic_source"],
                    "updatedAt": row["updated_at"],
                    "payload": payload,
                })
    return facts


def _latest_by_metric(facts: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    latest: Dict[str, Dict[str, Any]] = {}
    for fact in facts:
        code = fact.get("metricCode")
        if not code:
            continue
        if code not in latest:
            latest[code] = fact
    return latest


def _build_position(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "systemStoreCode": item.get("systemStoreCode"),
        "systemSpuCode": item.get("systemSpuCode"),
        "systemLinkCode": item.get("systemLinkCode"),
        "systemSkuCode": item.get("systemSkuCode"),
        "platform": item.get("platform"),
        "storeId": item.get("storeId") or item.get("normalizedStoreId"),
        "storeName": item.get("storeName") or item.get("store") or item.get("normalizedStoreName"),
        "productId": item.get("productId") or item.get("rawProductId"),
        "skuId": item.get("skuId"),
        "erpProductCode": item.get("erpProductCode"),
        "productLink": item.get("productLink") or item.get("link"),
        "archiveId": item.get("archiveId") or item.get("objectId") or item.get("id"),
        "sourceDataVersions": item.get("sourceDataVersions") or [],
        "sourceDatasets": item.get("sourceDatasets") or [],
    }


def _build_sections(item: Dict[str, Any], facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    latest = _latest_by_metric(facts)
    fallback = {
        "inventory_qty": item.get("inventory"),
        "avg_order_value": item.get("avgOrderValue") or item.get("price"),
        "payment_amount": item.get("paymentAmount"),
        "product_cost_amount": item.get("costAmount") or item.get("cost"),
        "gross_profit_amount": item.get("grossProfitAmount"),
        "gross_margin_rate": item.get("grossMargin"),
        "roi": item.get("roi"),
        "click_rate": item.get("clickRate"),
        "payment_conversion_rate": item.get("conversionRate"),
        "refund_rate": item.get("refundRate"),
        "ad_spend": item.get("adSpend"),
        "organic_visitor_count": item.get("organicVisitors"),
        "paid_visitor_count": item.get("paidVisitors"),
    }
    sections: List[Dict[str, Any]] = []
    for section_key, title, metrics in SECTION_RULES:
        if section_key == "identity":
            continue
        entries: List[Dict[str, Any]] = []
        for code in metrics:
            fact = latest.get(code)
            value = fact.get("displayValue") if fact else fallback.get(code)
            if value in {None, "", "—"}:
                continue
            entries.append({
                "metricCode": code,
                "metricName": METRIC_LABELS.get(code, code),
                "displayValue": value,
                "sourceSheet": fact.get("sourceSheet") if fact else "商品对象缓存",
                "dataVersion": fact.get("dataVersion") if fact else None,
                "statDate": fact.get("statDate") if fact else None,
                "factId": fact.get("factId") if fact else None,
            })
        sections.append({"key": section_key, "title": title, "items": entries})
    return sections


def _traffic_sources(facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for fact in facts:
        source = fact.get("trafficSource")
        if not source:
            continue
        grouped.setdefault(str(source), []).append(fact)
    result: List[Dict[str, Any]] = []
    for source, source_facts in grouped.items():
        latest = _latest_by_metric(source_facts)
        result.append({
            "trafficSource": source,
            "visitorCount": (latest.get("visitor_count") or {}).get("displayValue"),
            "clickRate": (latest.get("click_rate") or {}).get("displayValue"),
            "conversionRate": (latest.get("payment_conversion_rate") or {}).get("displayValue"),
            "roi": (latest.get("roi") or {}).get("displayValue"),
            "adSpend": (latest.get("ad_spend") or {}).get("displayValue"),
            "factCount": len(source_facts),
        })
    return sorted(result, key=lambda item: item.get("trafficSource") or "")


def _task_summary(item: Dict[str, Any]) -> Dict[str, Any]:
    has_active = bool(item.get("hasActiveTask") or item.get("activeTaskId"))
    has_completed = bool(item.get("completedTaskId"))
    return {
        "activeTaskId": item.get("activeTaskId"),
        "activeTaskStatus": item.get("activeTaskStatus"),
        "activeWorkflowStatus": item.get("activeWorkflowStatus"),
        "completedTaskId": item.get("completedTaskId"),
        "completedTaskStatus": item.get("completedTaskStatus"),
        "hasActiveTask": has_active,
        "taskCount": int(has_active) + int(has_completed),
        "summary": "当前有未完成任务" if has_active else "暂无未完成任务",
        "rule": "商品页只显示任务历史摘要，完整SOP在任务详情页查看。",
    }


def enrich_product_archive_detail(item: Dict[str, Any]) -> Dict[str, Any]:
    facts = _fetch_facts(item)
    enriched = dict(item)
    enriched["productArchiveDetailVersion"] = PRODUCT_ARCHIVE_DETAIL_VERSION
    enriched["productPosition"] = _build_position(enriched)
    enriched["metricSections"] = _build_sections(enriched, facts)
    enriched["trafficSourceFacts"] = _traffic_sources(facts)
    enriched["taskHistorySummary"] = _task_summary(enriched)
    enriched["metricFactSummary"] = {
        "factCount": len(facts),
        "productFactCount": len([fact for fact in facts if fact.get("factTable") == "product_metric_facts"]),
        "storeFactCount": len([fact for fact in facts if fact.get("factTable") == "store_metric_facts"]),
        "trafficFactCount": len([fact for fact in facts if fact.get("factTable") == "traffic_source_facts"]),
        "rule": "V12.1.2：商品详情读取独立事实表，payload.metricFacts 仅作为兼容缓存。",
    }
    return enriched
