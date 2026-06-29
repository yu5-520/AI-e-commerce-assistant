"""V14 signal pool service.

Signal Pool is the wide-intake radar between metric facts and RAG/Agent judgment.
It must never decide visible task creation by itself. Code records factual signals;
RAG supplies operating experience; Agent decides whether a signal becomes a task
snapshot, observation, data-gap task, or normal-wave record.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Tuple
from uuid import uuid4

from src.repositories.sqlite_repository import connect, dumps, ensure_columns, loads
from src.services.metric_fact_store_service import ensure_metric_fact_tables

SIGNAL_POOL_VERSION = "14.0.0"
TRACKED_METRICS = {
    "roi", "payment_amount", "ad_spend", "inventory_qty", "sellable_days",
    "payment_conversion_rate", "click_rate", "visitor_count", "page_view_count",
    "click_user_count", "organic_visitor_count", "paid_visitor_count",
    "gross_margin_rate", "refund_rate", "refund_amount", "payment_order_count",
    "payment_unit_count",
}


def now_iso() -> str:
    return datetime.now().isoformat()


def make_signal_id() -> str:
    return f"SIG-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:6].upper()}"


def _num(value: Any) -> float | None:
    if value in {None, "", "未识别", "—"}:
        return None
    try:
        return float(str(value).replace("¥", "").replace(",", "").replace("%", "").strip())
    except (TypeError, ValueError):
        return None


def _safe_date(value: Any) -> str:
    text = str(value or "").strip()
    return text[:10] if text else "未知日期"


def _change(old: float | None, new: float | None) -> float | None:
    if old is None or new is None or abs(old) < 1e-9:
        return None
    return (new - old) / abs(old)


def ensure_signal_pool_tables() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS signal_pool_v14 (
                signal_id TEXT PRIMARY KEY,
                data_version TEXT,
                entity_type TEXT,
                entity_id TEXT,
                store_id TEXT,
                signal_type TEXT NOT NULL,
                signal_strength TEXT,
                status TEXT NOT NULL,
                source_ref TEXT,
                payload TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        ensure_columns(conn, "signal_pool_v14", {"data_version": "TEXT", "entity_type": "TEXT", "entity_id": "TEXT", "store_id": "TEXT", "signal_strength": "TEXT", "source_ref": "TEXT", "updated_at": "TEXT"})
        conn.execute("CREATE INDEX IF NOT EXISTS idx_signal_pool_v14_version ON signal_pool_v14(data_version, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_signal_pool_v14_entity ON signal_pool_v14(entity_type, entity_id, store_id, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_signal_pool_v14_status ON signal_pool_v14(status, created_at)")
        conn.commit()


def _table_exists(conn: Any, table: str) -> bool:
    return bool(conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone())


def _load_metric_facts(data_version: str | None = None, limit: int = 12000) -> List[Dict[str, Any]]:
    """Load historical facts for comparison, while tagging this run with data_version.

    V14 does not filter to only the latest data_version because that would erase the
    multi-report comparison window. Tenant / account isolation is still handled at
    the API and repository scope; this demo-stage query keeps history visible so
    three uploaded reports can produce change signals.
    """
    ensure_metric_fact_tables()
    with connect() as conn:
        if not _table_exists(conn, "product_metric_facts"):
            return []
        rows = conn.execute(
            f"""
            SELECT *
            FROM product_metric_facts
            WHERE metric_code IN ({','.join('?' for _ in TRACKED_METRICS)})
            ORDER BY COALESCE(product_id, sku_id, erp_product_code, ''),
                     COALESCE(store_id, store_code, store_name, ''),
                     metric_code,
                     COALESCE(stat_date, updated_at) ASC,
                     updated_at ASC
            LIMIT ?
            """,
            [*sorted(TRACKED_METRICS), limit],
        ).fetchall()
    return [dict(row) for row in rows]


def _metric_signal_type(metric: str, latest: float | None, change_rate: float | None) -> tuple[str, str]:
    if metric == "inventory_qty" and latest is not None and latest <= 0:
        return "redline_inventory_zero", "high"
    if metric == "gross_margin_rate" and latest is not None and latest < 0.2:
        return "redline_margin_floor", "high"
    if metric == "refund_rate" and latest is not None and latest >= 0.12:
        return "redline_refund_floor", "high"
    if change_rate is None:
        return "metric_observed", "low"
    if abs(change_rate) >= 0.25:
        return "metric_large_wave", "medium"
    if abs(change_rate) >= 0.08:
        return "metric_small_wave", "low"
    return "normal_wave_candidate", "low"


def _group_facts(facts: List[Dict[str, Any]]) -> Dict[Tuple[str, str | None], Dict[str, List[Dict[str, Any]]]]:
    grouped: Dict[Tuple[str, str | None], Dict[str, List[Dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in facts:
        product_id = str(row.get("product_id") or row.get("sku_id") or row.get("erp_product_code") or "").strip()
        if not product_id:
            continue
        store_id = str(row.get("store_id") or row.get("store_code") or row.get("store_name") or "").strip() or None
        metric = str(row.get("metric_code") or "").strip()
        if metric in TRACKED_METRICS:
            grouped[(product_id, store_id)][metric].append(row)
    for metrics in grouped.values():
        for rows in metrics.values():
            rows.sort(key=lambda item: (_safe_date(item.get("stat_date") or item.get("updated_at")), str(item.get("updated_at") or "")))
    return grouped


def _build_signal(product_id: str, store_id: str | None, metric: str, rows: List[Dict[str, Any]], data_version: str | None) -> Dict[str, Any]:
    first = rows[0]
    latest = rows[-1]
    first_value = _num(first.get("metric_value"))
    latest_value = _num(latest.get("metric_value"))
    change_rate = _change(first_value, latest_value)
    signal_type, strength = _metric_signal_type(metric, latest_value, change_rate)
    return {
        "version": SIGNAL_POOL_VERSION,
        "signalId": make_signal_id(),
        "dataVersion": data_version or latest.get("data_version"),
        "latestSourceDataVersion": latest.get("data_version"),
        "entityType": "product",
        "entityId": product_id,
        "productId": product_id,
        "storeId": store_id,
        "signalType": signal_type,
        "signalStrength": strength,
        "metricCode": metric,
        "firstValue": first_value,
        "latestValue": latest_value,
        "firstDisplayValue": first.get("display_value") or first.get("raw_value"),
        "latestDisplayValue": latest.get("display_value") or latest.get("raw_value"),
        "firstDate": _safe_date(first.get("stat_date") or first.get("updated_at")),
        "latestDate": _safe_date(latest.get("stat_date") or latest.get("updated_at")),
        "changeRate": change_rate,
        "sourceRows": len(rows),
        "sourceSheet": latest.get("source_sheet"),
        "sourceBlockId": latest.get("source_block_id"),
        "status": "pending_rag_agent",
        "rule": "V14：信号池宽进，只记录事实变化和风险提示；是否生成任务由RAG增强后的Agent判断。",
    }


def _build_data_gap_signals(facts: List[Dict[str, Any]], data_version: str | None) -> List[Dict[str, Any]]:
    missing_anchor = 0
    missing_date = 0
    for row in facts:
        product_id = str(row.get("product_id") or row.get("sku_id") or row.get("erp_product_code") or "").strip()
        if not product_id:
            missing_anchor += 1
        if _safe_date(row.get("stat_date") or row.get("updated_at")) == "未知日期":
            missing_date += 1
    gaps: List[Dict[str, Any]] = []
    for gap_type, count, reason in [
        ("data_gap_missing_product_anchor", missing_anchor, "部分指标事实缺少商品ID/SKU/ERP商品编码，无法稳定归属到商品。"),
        ("data_gap_missing_stat_date", missing_date, "部分指标事实缺少统计日期，无法稳定比较趋势。"),
    ]:
        if count <= 0:
            continue
        gaps.append({"version": SIGNAL_POOL_VERSION, "signalId": make_signal_id(), "dataVersion": data_version, "entityType": "report", "entityId": data_version or "latest", "productId": None, "storeId": None, "signalType": gap_type, "signalStrength": "medium", "metricCode": "data_quality", "gapCount": count, "reason": reason, "status": "pending_rag_agent", "rule": "V14：数据缺口也是信号，可由Agent生成补数/复核任务，而不是被任务门槛吞掉。"})
    return gaps


def _save_signal(signal: Dict[str, Any]) -> Dict[str, Any]:
    ensure_signal_pool_tables()
    created_at = now_iso()
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO signal_pool_v14 (
                signal_id, data_version, entity_type, entity_id, store_id, signal_type,
                signal_strength, status, source_ref, payload, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (signal["signalId"], signal.get("dataVersion"), signal.get("entityType"), signal.get("entityId"), signal.get("storeId"), signal.get("signalType"), signal.get("signalStrength"), signal.get("status") or "pending_rag_agent", signal.get("sourceRef") or f"metric_facts:{signal.get('dataVersion') or 'latest'}", dumps(signal), created_at, created_at),
        )
        conn.commit()
    return signal


def row_to_signal(row: Any) -> Dict[str, Any]:
    payload = loads(row["payload"])
    return {**payload, "signalId": row["signal_id"], "dataVersion": row["data_version"], "entityType": row["entity_type"], "entityId": row["entity_id"], "storeId": row["store_id"], "signalType": row["signal_type"], "signalStrength": row["signal_strength"], "status": row["status"], "createdAt": row["created_at"], "updatedAt": row["updated_at"]}


def list_signals(data_version: str | None = None, status: str | None = None, limit: int = 200) -> Dict[str, Any]:
    ensure_signal_pool_tables()
    clauses = []
    params: List[Any] = []
    if data_version:
        clauses.append("data_version = ?")
        params.append(data_version)
    if status:
        clauses.append("status = ?")
        params.append(status)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM signal_pool_v14 {where} ORDER BY created_at DESC LIMIT ?", [*params, limit]).fetchall()
    items = [row_to_signal(row) for row in rows]
    by_type: Dict[str, int] = defaultdict(int)
    for item in items:
        by_type[str(item.get("signalType"))] += 1
    return {"version": SIGNAL_POOL_VERSION, "dataVersion": data_version, "signalCount": len(items), "byType": dict(by_type), "signals": items}


def generate_signal_pool(data_version: str | None = None, *, max_signals: int = 200) -> Dict[str, Any]:
    """Generate wide-intake signals from metric facts without creating tasks."""
    ensure_signal_pool_tables()
    facts = _load_metric_facts(data_version=data_version)
    grouped = _group_facts(facts)
    signals: List[Dict[str, Any]] = []
    for (product_id, store_id), metrics in grouped.items():
        for metric, rows in metrics.items():
            if rows:
                signals.append(_build_signal(product_id, store_id, metric, rows, data_version))
    signals.extend(_build_data_gap_signals(facts, data_version))
    strength_rank = {"high": 0, "medium": 1, "low": 2}
    signals.sort(key=lambda item: (strength_rank.get(str(item.get("signalStrength")), 9), item.get("entityId") or "", item.get("metricCode") or ""))
    saved = [_save_signal(signal) for signal in signals[:max_signals]]
    by_type: Dict[str, int] = defaultdict(int)
    by_strength: Dict[str, int] = defaultdict(int)
    for signal in saved:
        by_type[str(signal.get("signalType"))] += 1
        by_strength[str(signal.get("signalStrength"))] += 1
    ref = f"signal_pool:{data_version or 'latest'}"
    return {"version": SIGNAL_POOL_VERSION, "mode": "wide_signal_pool_no_task_creation", "dataVersion": data_version, "taskSignalRef": ref, "outputRef": ref, "signalCount": len(saved), "createdTaskCount": 0, "byType": dict(by_type), "byStrength": dict(by_strength), "signals": saved, "rule": "V14：task_signal_station只生成信号池，不再绕过RAG/Agent直接创建任务。"}
