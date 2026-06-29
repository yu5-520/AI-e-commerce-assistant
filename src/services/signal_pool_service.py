"""V14.1 signal pool service."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Tuple

from src.repositories.sqlite_repository import connect, dumps, ensure_columns, loads
from src.services.metric_fact_store_service import ensure_metric_fact_tables

SIGNAL_POOL_VERSION = "14.1.0"
TRACKED_METRICS = {
    "roi", "payment_amount", "ad_spend", "inventory_qty", "sellable_days",
    "payment_conversion_rate", "click_rate", "visitor_count", "page_view_count",
    "click_user_count", "organic_visitor_count", "paid_visitor_count",
    "gross_margin_rate", "refund_rate", "refund_amount", "payment_order_count",
    "payment_unit_count",
}


def now_iso() -> str:
    return datetime.now().isoformat()


def make_signal_id(seed: str) -> str:
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:14].upper()
    return f"SIG-{digest}"


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
    first_date = _safe_date(first.get("stat_date") or first.get("updated_at"))
    latest_date = _safe_date(latest.get("stat_date") or latest.get("updated_at"))
    seed = "|".join([str(data_version or latest.get("data_version") or "latest"), product_id, str(store_id or ""), metric, signal_type, first_date, latest_date, str(latest_value)])
    return {
        "version": SIGNAL_POOL_VERSION,
        "signalId": make_signal_id(seed),
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
        "firstDate": first_date,
        "latestDate": latest_date,
        "changeRate": change_rate,
        "sourceRows": len(rows),
        "sourceSheet": latest.get("source_sheet"),
        "sourceBlockId": latest.get("source_block_id"),
        "status": "pending_rag_agent",
        "rule": "V14.1 signal pool is wide intake; judgment happens after RAG context.",
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
        ("data_gap_missing_product_anchor", missing_anchor, "missing product anchor"),
        ("data_gap_missing_stat_date", missing_date, "missing stat date"),
    ]:
        if count <= 0:
            continue
        seed = f"{data_version or 'latest'}|{gap_type}|{count}"
        gaps.append({"version": SIGNAL_POOL_VERSION, "signalId": make_signal_id(seed), "dataVersion": data_version, "entityType": "report", "entityId": data_version or "latest", "productId": None, "storeId": None, "signalType": gap_type, "signalStrength": "medium", "metricCode": "data_quality", "gapCount": count, "reason": reason, "status": "pending_rag_agent", "rule": "V14.1 data gaps are signals."})
    return gaps


def _save_signal(signal: Dict[str, Any]) -> Dict[str, Any]:
    ensure_signal_pool_tables()
    now = now_iso()
    with connect() as conn:
        existing = conn.execute("SELECT * FROM signal_pool_v14 WHERE signal_id = ?", (signal["signalId"],)).fetchone()
        status = (existing["status"] if existing else None) or signal.get("status") or "pending_rag_agent"
        created_at = existing["created_at"] if existing else now
        conn.execute(
            """
            INSERT OR REPLACE INTO signal_pool_v14 (signal_id, data_version, entity_type, entity_id, store_id, signal_type, signal_strength, status, source_ref, payload, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (signal["signalId"], signal.get("dataVersion"), signal.get("entityType"), signal.get("entityId"), signal.get("storeId"), signal.get("signalType"), signal.get("signalStrength"), status, signal.get("sourceRef") or f"metric_facts:{signal.get('dataVersion') or 'latest'}", dumps({**signal, "status": status}), created_at, now),
        )
        conn.commit()
    signal["status"] = status
    return signal


def update_signal_status(signal_id: str | None, status: str, patch: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
    if not signal_id:
        return None
    ensure_signal_pool_tables()
    with connect() as conn:
        row = conn.execute("SELECT * FROM signal_pool_v14 WHERE signal_id = ?", (signal_id,)).fetchone()
        if not row:
            return None
        payload = loads(row["payload"])
        payload.update(patch or {})
        payload["status"] = status
        payload["updatedAt"] = now_iso()
        conn.execute("UPDATE signal_pool_v14 SET status = ?, payload = ?, updated_at = ? WHERE signal_id = ?", (status, dumps(payload), payload["updatedAt"], signal_id))
        conn.commit()
        row = conn.execute("SELECT * FROM signal_pool_v14 WHERE signal_id = ?", (signal_id,)).fetchone()
    return row_to_signal(row) if row else None


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
    by_status: Dict[str, int] = defaultdict(int)
    for item in items:
        by_type[str(item.get("signalType"))] += 1
        by_status[str(item.get("status"))] += 1
    return {"version": SIGNAL_POOL_VERSION, "dataVersion": data_version, "signalCount": len(items), "byType": dict(by_type), "byStatus": dict(by_status), "signals": items}


def generate_signal_pool(data_version: str | None = None, *, max_signals: int = 200) -> Dict[str, Any]:
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
    by_status: Dict[str, int] = defaultdict(int)
    for signal in saved:
        by_type[str(signal.get("signalType"))] += 1
        by_strength[str(signal.get("signalStrength"))] += 1
        by_status[str(signal.get("status"))] += 1
    ref = f"signal_pool:{data_version or 'latest'}"
    return {"version": SIGNAL_POOL_VERSION, "mode": "wide_signal_pool_no_task_creation", "dataVersion": data_version, "taskSignalRef": ref, "outputRef": ref, "signalCount": len(saved), "createdTaskCount": 0, "byType": dict(by_type), "byStrength": dict(by_strength), "byStatus": dict(by_status), "signals": saved, "rule": "V14.1 signal station writes signal_pool only."}
