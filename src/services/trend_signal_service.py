"""V6.1 product snapshot, metric trend, and business signal service.

V6.0 unified report import solved the data entrance problem. V6.1 turns each
classified import result into product time snapshots, calculates metric changes
against the previous snapshot, and records business signals for the trend center.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List
from uuid import uuid4

from src.repositories.sqlite_repository import connect, dumps, loads
from src.services.account_service import visible_store_ids_for_user

TREND_VERSION = "6.1.0"

METRIC_FIELDS: Dict[str, str] = {
    "stock": "库存",
    "available_stock": "可用库存",
    "safety_stock": "安全库存",
    "sale_price": "售价",
    "cost_price": "成本",
    "gross_margin": "毛利率",
    "roi": "ROI",
    "traffic": "流量",
    "clicks": "点击量",
    "ctr": "点击率",
    "conversion_rate": "转化率",
    "ad_spend": "投放花费",
    "sales_volume": "销量",
    "quantity": "销量",
    "revenue": "销售额",
    "actual_paid": "销售额",
    "refund_amount": "退款金额",
    "refund_count": "退款次数",
    "refund_rate": "退款率",
    "good_review_rate": "好评率",
    "bad_review_rate": "差评率",
}

POSITIVE_METRICS = {"roi", "traffic", "clicks", "ctr", "conversion_rate", "gross_margin", "sales_volume", "quantity", "revenue", "actual_paid", "good_review_rate"}
NEGATIVE_METRICS = {"refund_amount", "refund_count", "refund_rate", "bad_review_rate"}
STOCK_METRICS = {"stock", "available_stock"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}".upper()


def _pick(row: Dict[str, Any], *fields: str, default: Any = None) -> Any:
    for field in fields:
        if row.get(field) not in {None, ""}:
            return row.get(field)
    return default


def _as_float(value: Any, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    text = str(value).replace(",", "").replace("%", "").replace("¥", "").strip()
    try:
        return float(text)
    except (TypeError, ValueError):
        return default


def _normalize_ratio(metric_name: str, value: float | None) -> float | None:
    if value is None:
        return None
    if metric_name in {"ctr", "conversion_rate", "gross_margin", "refund_rate", "good_review_rate", "bad_review_rate"} and value > 1:
        return value / 100
    return value


def ensure_trend_tables() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS product_master_v6 (
                product_id TEXT PRIMARY KEY,
                store_id TEXT,
                store_name TEXT,
                platform TEXT,
                category TEXT,
                title TEXT,
                payload TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS product_snapshots_v6 (
                snapshot_id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                store_id TEXT,
                data_version TEXT NOT NULL,
                dataset_name TEXT NOT NULL,
                source_system TEXT,
                snapshot_at TEXT NOT NULL,
                metrics TEXT,
                payload TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS metric_trends_v6 (
                trend_id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                store_id TEXT,
                metric_name TEXT NOT NULL,
                metric_label TEXT,
                previous_value REAL,
                current_value REAL,
                change_value REAL,
                change_rate REAL,
                trend_direction TEXT,
                window_type TEXT,
                data_version TEXT,
                payload TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS business_signals_v6 (
                signal_id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                store_id TEXT,
                signal_type TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                source_metric TEXT,
                trend_direction TEXT,
                data_version TEXT,
                task_candidate INTEGER DEFAULT 0,
                payload TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_product_snapshots_product_time_v6 ON product_snapshots_v6(product_id, store_id, snapshot_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_metric_trends_product_v6 ON metric_trends_v6(product_id, store_id, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_business_signals_product_v6 ON business_signals_v6(product_id, store_id, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_business_signals_store_v6 ON business_signals_v6(store_id, created_at)")
        conn.commit()


def _product_id(row: Dict[str, Any]) -> str | None:
    value = _pick(row, "product_id", "商品ID", "sku", "SKU", "商品编码", "商家编码")
    return str(value).strip() if value not in {None, ""} else None


def _store_id(row: Dict[str, Any]) -> str | None:
    value = _pick(row, "store_id", "storeId", "店铺ID", "店铺id")
    return str(value).strip() if value not in {None, ""} else None


def _metric_values(row: Dict[str, Any]) -> Dict[str, float]:
    values: Dict[str, float] = {}
    for metric in METRIC_FIELDS:
        value = _as_float(row.get(metric))
        value = _normalize_ratio(metric, value)
        if value is not None:
            values[metric] = value
    if "gross_margin" not in values:
        sale = values.get("sale_price")
        cost = values.get("cost_price")
        if sale and cost is not None and sale > 0:
            values["gross_margin"] = (sale - cost) / sale
    if "revenue" not in values and "actual_paid" in values:
        values["revenue"] = values["actual_paid"]
    if "sales_volume" not in values and "quantity" in values:
        values["sales_volume"] = values["quantity"]
    return values


def _upsert_product_master(row: Dict[str, Any], product_id: str, store_id: str | None, created_at: str) -> None:
    title = _pick(row, "product_name", "商品名称", "商品标题", "title", "标题", default=f"报表商品 {product_id}")
    store_name = _pick(row, "store_name", "store", "店铺", "店铺名称")
    platform = _pick(row, "platform", "平台")
    category = _pick(row, "category", "类目", "商品类目")
    payload = {"productId": product_id, "storeId": store_id, "title": title, "storeName": store_name, "platform": platform, "category": category}
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO product_master_v6 (product_id, store_id, store_name, platform, category, title, payload, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(product_id) DO UPDATE SET
                store_id=COALESCE(excluded.store_id, product_master_v6.store_id),
                store_name=COALESCE(excluded.store_name, product_master_v6.store_name),
                platform=COALESCE(excluded.platform, product_master_v6.platform),
                category=COALESCE(excluded.category, product_master_v6.category),
                title=COALESCE(excluded.title, product_master_v6.title),
                payload=excluded.payload,
                updated_at=excluded.updated_at
            """,
            (product_id, store_id, store_name, platform, category, title, dumps(payload), created_at, created_at),
        )
        conn.commit()


def _latest_snapshot(product_id: str, store_id: str | None, before_data_version: str) -> Dict[str, Any] | None:
    ensure_trend_tables()
    if store_id:
        query = """
            SELECT * FROM product_snapshots_v6
            WHERE product_id = ? AND store_id = ? AND data_version != ?
            ORDER BY snapshot_at DESC LIMIT 1
        """
        params: tuple[Any, ...] = (product_id, store_id, before_data_version)
    else:
        query = """
            SELECT * FROM product_snapshots_v6
            WHERE product_id = ? AND data_version != ?
            ORDER BY snapshot_at DESC LIMIT 1
        """
        params = (product_id, before_data_version)
    with connect() as conn:
        row = conn.execute(query, params).fetchone()
    if not row:
        return None
    return dict(row)


def _trend_direction(metric: str, previous: float, current: float) -> tuple[str, float, float]:
    change_value = current - previous
    change_rate = change_value / abs(previous) if previous not in {0, 0.0} else 0.0
    if abs(change_rate) < 0.03:
        direction = "stable"
    elif change_rate > 0:
        direction = "up"
    else:
        direction = "down"
    return direction, change_value, change_rate


def _signal_from_trend(trend: Dict[str, Any]) -> Dict[str, Any] | None:
    metric = trend["metricName"]
    direction = trend["trendDirection"]
    rate = trend.get("changeRate") or 0
    current = trend.get("currentValue")
    if metric in STOCK_METRICS and direction == "down" and rate <= -0.2:
        return {"signalType": "库存下降信号", "riskLevel": "中", "taskCandidate": True, "reason": "库存较上次快照下降超过 20%，需要进入库存观察或补货判断。"}
    if metric == "roi" and direction == "down" and rate <= -0.15:
        return {"signalType": "ROI 下滑信号", "riskLevel": "中", "taskCandidate": True, "reason": "ROI 较上次快照下降超过 15%，需要结合流量和转化率排查。"}
    if metric in {"traffic", "clicks", "ctr", "conversion_rate", "sales_volume", "revenue"} and direction == "up" and rate >= 0.15:
        return {"signalType": "增长信号", "riskLevel": "低", "taskCandidate": False, "reason": f"{METRIC_FIELDS.get(metric, metric)} 较上次快照增长超过 15%，进入趋势中心观察。"}
    if metric in {"gross_margin", "good_review_rate"} and direction == "up" and rate >= 0.05:
        return {"signalType": "质量改善信号", "riskLevel": "低", "taskCandidate": False, "reason": f"{METRIC_FIELDS.get(metric, metric)} 有改善趋势。"}
    if metric in NEGATIVE_METRICS and direction == "up" and rate >= 0.1:
        return {"signalType": "售后风险信号", "riskLevel": "中", "taskCandidate": True, "reason": f"{METRIC_FIELDS.get(metric, metric)} 上升，需避免继续放大投产。"}
    if metric == "gross_margin" and current is not None and current < 0.2:
        return {"signalType": "毛利红线信号", "riskLevel": "高", "taskCandidate": True, "reason": "毛利率低于 20% 演示红线，V6.2 后需接 RAG 指标门控。"}
    return None


def _insert_snapshot(product_id: str, store_id: str | None, data_version: str, dataset_name: str, source_system: str | None, metrics: Dict[str, float], row: Dict[str, Any], created_at: str) -> str:
    snapshot_id = make_id("PSNAP")
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO product_snapshots_v6 (snapshot_id, product_id, store_id, data_version, dataset_name, source_system, snapshot_at, metrics, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (snapshot_id, product_id, store_id, data_version, dataset_name, source_system, created_at, dumps(metrics), dumps({"row": row, "version": TREND_VERSION})),
        )
        conn.commit()
    return snapshot_id


def _insert_trend(trend: Dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO metric_trends_v6 (
                trend_id, product_id, store_id, metric_name, metric_label, previous_value, current_value,
                change_value, change_rate, trend_direction, window_type, data_version, payload, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trend["trendId"], trend["productId"], trend.get("storeId"), trend["metricName"], trend["metricLabel"],
                trend.get("previousValue"), trend.get("currentValue"), trend.get("changeValue"), trend.get("changeRate"),
                trend["trendDirection"], trend.get("windowType") or "last_snapshot", trend.get("dataVersion"), dumps(trend), trend["createdAt"],
            ),
        )
        conn.commit()


def _insert_signal(signal: Dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO business_signals_v6 (
                signal_id, product_id, store_id, signal_type, risk_level, source_metric, trend_direction,
                data_version, task_candidate, payload, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                signal["signalId"], signal["productId"], signal.get("storeId"), signal["signalType"], signal["riskLevel"],
                signal.get("sourceMetric"), signal.get("trendDirection"), signal.get("dataVersion"), 1 if signal.get("taskCandidate") else 0,
                dumps(signal), signal["createdAt"],
            ),
        )
        conn.commit()


def ingest_product_trends(
    *,
    dataset_name: str,
    data_version: str,
    rows: Iterable[Dict[str, Any]],
    source_system: str | None = None,
) -> Dict[str, Any]:
    """Persist product snapshots and generate metric trends/signals for one imported dataset."""
    ensure_trend_tables()
    created_at = now_iso()
    snapshot_count = 0
    trends: List[Dict[str, Any]] = []
    signals: List[Dict[str, Any]] = []
    product_ids: List[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        product_id = _product_id(row)
        if not product_id:
            continue
        store_id = _store_id(row)
        metrics = _metric_values(row)
        if not metrics:
            continue
        product_ids.append(product_id)
        _upsert_product_master(row, product_id, store_id, created_at)
        previous = _latest_snapshot(product_id, store_id, data_version)
        previous_metrics = loads(previous.get("metrics")) if previous else {}
        snapshot_id = _insert_snapshot(product_id, store_id, data_version, dataset_name, source_system, metrics, row, created_at)
        snapshot_count += 1
        for metric_name, current_value in metrics.items():
            if metric_name not in previous_metrics:
                continue
            previous_value = _as_float(previous_metrics.get(metric_name))
            if previous_value is None:
                continue
            direction, change_value, change_rate = _trend_direction(metric_name, previous_value, current_value)
            trend = {
                "version": TREND_VERSION,
                "trendId": make_id("TREND"),
                "snapshotId": snapshot_id,
                "productId": product_id,
                "storeId": store_id,
                "metricName": metric_name,
                "metricLabel": METRIC_FIELDS.get(metric_name, metric_name),
                "previousValue": previous_value,
                "currentValue": current_value,
                "changeValue": change_value,
                "changeRate": change_rate,
                "trendDirection": direction,
                "windowType": "last_snapshot",
                "dataVersion": data_version,
                "datasetName": dataset_name,
                "createdAt": created_at,
            }
            _insert_trend(trend)
            trends.append(trend)
            signal_base = _signal_from_trend(trend)
            if signal_base:
                signal = {
                    "version": TREND_VERSION,
                    "signalId": make_id("SIGNAL"),
                    "productId": product_id,
                    "storeId": store_id,
                    "signalType": signal_base["signalType"],
                    "riskLevel": signal_base["riskLevel"],
                    "sourceMetric": metric_name,
                    "metricLabel": METRIC_FIELDS.get(metric_name, metric_name),
                    "trendDirection": direction,
                    "changeRate": change_rate,
                    "dataVersion": data_version,
                    "datasetName": dataset_name,
                    "taskCandidate": signal_base["taskCandidate"],
                    "reason": signal_base["reason"],
                    "createdAt": created_at,
                }
                _insert_signal(signal)
                signals.append(signal)
    return {
        "version": TREND_VERSION,
        "datasetName": dataset_name,
        "dataVersion": data_version,
        "sourceSystem": source_system,
        "snapshotCount": snapshot_count,
        "trendCount": len(trends),
        "signalCount": len(signals),
        "taskCandidateSignalCount": len([item for item in signals if item.get("taskCandidate")]),
        "productCount": len(set(product_ids)),
        "sampleTrends": trends[:8],
        "sampleSignals": signals[:8],
        "rule": "V6.1 先生成商品时间快照、指标变化和经营信号；V6.2 再把信号接入风险分级任务。",
    }


def _row_payload(row: Any) -> Dict[str, Any]:
    payload = loads(row["payload"])
    return payload if payload else dict(row)


def _allowed_store_clause(user_id: str | None) -> tuple[str, List[Any]]:
    if not user_id:
        return "", []
    allowed = visible_store_ids_for_user(user_id)
    if not allowed:
        return " AND 1=0", []
    placeholders = ",".join("?" for _ in allowed)
    return f" AND (store_id IS NULL OR store_id IN ({placeholders}))", list(allowed)


def trend_center_summary(user_id: str | None = None, limit: int = 30) -> Dict[str, Any]:
    ensure_trend_tables()
    store_clause, params = _allowed_store_clause(user_id)
    with connect() as conn:
        products = conn.execute(f"SELECT * FROM product_master_v6 WHERE 1=1{store_clause} ORDER BY updated_at DESC LIMIT ?", [*params, limit]).fetchall()
        snapshots = conn.execute(f"SELECT * FROM product_snapshots_v6 WHERE 1=1{store_clause} ORDER BY snapshot_at DESC LIMIT ?", [*params, limit]).fetchall()
        trends = conn.execute(f"SELECT * FROM metric_trends_v6 WHERE 1=1{store_clause} ORDER BY created_at DESC LIMIT ?", [*params, limit]).fetchall()
        signals = conn.execute(f"SELECT * FROM business_signals_v6 WHERE 1=1{store_clause} ORDER BY created_at DESC LIMIT ?", [*params, limit]).fetchall()
    trend_items = [_row_payload(row) for row in trends]
    signal_items = [_row_payload(row) for row in signals]
    product_items = [_row_payload(row) for row in products]
    snapshots_by_product: Dict[str, int] = defaultdict(int)
    for row in snapshots:
        snapshots_by_product[row["product_id"]] += 1
    store_summary: Dict[str, int] = defaultdict(int)
    platform_summary: Dict[str, int] = defaultdict(int)
    category_summary: Dict[str, int] = defaultdict(int)
    for item in product_items:
        store_summary[str(item.get("storeName") or item.get("storeId") or "未绑定店铺")] += 1
        platform_summary[str(item.get("platform") or "未知平台")] += 1
        category_summary[str(item.get("category") or "未分类")] += 1
    signal_by_level: Dict[str, int] = defaultdict(int)
    signal_by_type: Dict[str, int] = defaultdict(int)
    for item in signal_items:
        signal_by_level[str(item.get("riskLevel") or "低")] += 1
        signal_by_type[str(item.get("signalType") or "经营信号")] += 1
    return {
        "version": TREND_VERSION,
        "name": "V6.1 动态数据趋势中心",
        "summary": {
            "productCount": len(product_items),
            "snapshotCount": len(snapshots),
            "trendCount": len(trend_items),
            "signalCount": len(signal_items),
            "taskCandidateSignalCount": len([item for item in signal_items if item.get("taskCandidate")]),
        },
        "storeTrends": [{"name": key, "count": value} for key, value in sorted(store_summary.items(), key=lambda item: item[1], reverse=True)],
        "platformTrends": [{"name": key, "count": value} for key, value in sorted(platform_summary.items(), key=lambda item: item[1], reverse=True)],
        "categoryTrends": [{"name": key, "count": value} for key, value in sorted(category_summary.items(), key=lambda item: item[1], reverse=True)],
        "signalByLevel": dict(signal_by_level),
        "signalByType": dict(signal_by_type),
        "latestProducts": [{**item, "snapshotCount": snapshots_by_product.get(item.get("productId") or item.get("product_id"), 0)} for item in product_items[:12]],
        "latestTrends": trend_items[:12],
        "latestSignals": signal_items[:12],
        "rule": "趋势中心展示总店铺、单商品、平台、类目的趋势支撑；V6.2 将基于风险分级生成任务。",
    }
