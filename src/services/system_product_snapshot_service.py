"""V14.2 system product snapshot service.

This service freezes the same product state used by the product module. Signals
must compare these snapshots instead of scanning a different low-level source.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from src.repositories.sqlite_repository import connect, dumps, ensure_columns, loads
from src.services.module_projection_service import projected_products

SYSTEM_PRODUCT_SNAPSHOT_VERSION = "14.2.0"

SNAPSHOT_FIELDS = [
    "inventory",
    "paymentAmount",
    "grossMargin",
    "roi",
    "clickRate",
    "conversionRate",
    "refundRate",
    "adSpend",
    "organicVisitors",
    "paidVisitors",
    "inventoryStatus",
    "afterSales",
]


def now_iso() -> str:
    return datetime.now().isoformat()


def ensure_product_snapshot_tables() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS system_product_snapshots_v14 (
                snapshot_id TEXT PRIMARY KEY,
                data_version TEXT,
                product_count INTEGER DEFAULT 0,
                payload TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        ensure_columns(conn, "system_product_snapshots_v14", {"data_version": "TEXT", "product_count": "INTEGER DEFAULT 0", "updated_at": "TEXT"})
        conn.execute("CREATE INDEX IF NOT EXISTS idx_system_product_snapshot_v14_version ON system_product_snapshots_v14(data_version, created_at)")
        conn.commit()


def snapshot_id_for(data_version: str | None) -> str:
    return f"PRODUCT-SNAPSHOT-{data_version or 'latest'}"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _product_key(item: Dict[str, Any]) -> str:
    return _text(item.get("objectId")) or f"{_text(item.get('storeId')) or 'GLOBAL'}::{_text(item.get('productId') or item.get('id'))}"


def _snapshot_item(item: Dict[str, Any]) -> Dict[str, Any]:
    next_item = {
        "objectId": _product_key(item),
        "productId": item.get("productId") or item.get("id"),
        "storeId": item.get("storeId"),
        "storeName": item.get("storeName") or item.get("store"),
        "title": item.get("title"),
        "shortName": item.get("shortName"),
        "platform": item.get("platform"),
        "sourceDataVersions": item.get("sourceDataVersions") or [],
        "sourceDatasets": item.get("sourceDatasets") or [],
        "metricFacts": item.get("metricFacts") or [],
    }
    for field in SNAPSHOT_FIELDS:
        next_item[field] = item.get(field)
    return next_item


def row_to_snapshot(row: Any) -> Dict[str, Any]:
    payload = loads(row["payload"])
    return {
        **payload,
        "snapshotId": row["snapshot_id"],
        "dataVersion": row["data_version"],
        "productCount": int(row["product_count"] or 0),
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def get_product_snapshot(data_version: str | None = None) -> Dict[str, Any] | None:
    ensure_product_snapshot_tables()
    with connect() as conn:
        if data_version:
            row = conn.execute("SELECT * FROM system_product_snapshots_v14 WHERE data_version = ? ORDER BY created_at DESC LIMIT 1", (data_version,)).fetchone()
        else:
            row = conn.execute("SELECT * FROM system_product_snapshots_v14 ORDER BY created_at DESC LIMIT 1").fetchone()
    return row_to_snapshot(row) if row else None


def previous_product_snapshot(data_version: str | None = None) -> Dict[str, Any] | None:
    ensure_product_snapshot_tables()
    with connect() as conn:
        if data_version:
            row = conn.execute("SELECT * FROM system_product_snapshots_v14 WHERE data_version != ? ORDER BY created_at DESC LIMIT 1", (data_version,)).fetchone()
        else:
            rows = conn.execute("SELECT * FROM system_product_snapshots_v14 ORDER BY created_at DESC LIMIT 2").fetchall()
            row = rows[1] if len(rows) > 1 else None
    return row_to_snapshot(row) if row else None


def materialize_system_product_snapshot(data_version: str | None = None, *, user_id: str | None = None, force: bool = True) -> Dict[str, Any]:
    ensure_product_snapshot_tables()
    snapshot_id = snapshot_id_for(data_version)
    if not force:
        existing = get_product_snapshot(data_version)
        if existing:
            return {**existing, "idempotentHit": True}
    products = [_snapshot_item(item) for item in projected_products(user_id)]
    if data_version:
        filtered = []
        for item in products:
            versions = item.get("sourceDataVersions") or []
            if not versions or data_version in versions:
                filtered.append(item)
        if filtered:
            products = filtered
    payload = {
        "version": SYSTEM_PRODUCT_SNAPSHOT_VERSION,
        "snapshotId": snapshot_id,
        "dataVersion": data_version,
        "stationId": "system_product_snapshot_station",
        "products": products,
        "productCount": len(products),
        "fieldSet": SNAPSHOT_FIELDS,
        "source": "module_projection_service.projected_products",
        "rule": "V14.2 product signals compare system product snapshots, not a separate fact-table scan.",
    }
    now = now_iso()
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO system_product_snapshots_v14 (snapshot_id, data_version, product_count, payload, created_at, updated_at)
            VALUES (?, ?, ?, ?, COALESCE((SELECT created_at FROM system_product_snapshots_v14 WHERE snapshot_id = ?), ?), ?)
            """,
            (snapshot_id, data_version, len(products), dumps(payload), snapshot_id, now, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM system_product_snapshots_v14 WHERE snapshot_id = ?", (snapshot_id,)).fetchone()
    return {**row_to_snapshot(row), "outputRef": f"system_product_snapshot:{snapshot_id}", "productSnapshotRef": f"system_product_snapshot:{snapshot_id}"}


def product_snapshot_summary(limit: int = 20) -> Dict[str, Any]:
    ensure_product_snapshot_tables()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM system_product_snapshots_v14 ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    items = [row_to_snapshot(row) for row in rows]
    return {"version": SYSTEM_PRODUCT_SNAPSHOT_VERSION, "snapshotCount": len(items), "latest": items[0] if items else None, "items": items}
