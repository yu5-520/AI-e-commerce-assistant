"""V14.3 signal pool service.

Signal Pool consumes full product signal packages. Normal products are not
dropped before Agent judgment; normal_state packages are still queued.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

from src.repositories.sqlite_repository import connect, dumps, ensure_columns, loads
from src.services.product_signal_snapshot_service import materialize_product_signal_snapshot

SIGNAL_POOL_VERSION = "14.3.0"


def now_iso() -> str:
    return datetime.now().isoformat()


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


def _save_signal(signal: Dict[str, Any]) -> Dict[str, Any]:
    ensure_signal_pool_tables()
    now = now_iso()
    signal_id = signal["signalId"]
    with connect() as conn:
        existing = conn.execute("SELECT * FROM signal_pool_v14 WHERE signal_id = ?", (signal_id,)).fetchone()
        status = (existing["status"] if existing else None) or signal.get("status") or "pending_rag_agent"
        created_at = existing["created_at"] if existing else now
        payload = {**signal, "version": SIGNAL_POOL_VERSION, "status": status}
        conn.execute(
            """
            INSERT OR REPLACE INTO signal_pool_v14 (signal_id, data_version, entity_type, entity_id, store_id, signal_type, signal_strength, status, source_ref, payload, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (signal_id, signal.get("dataVersion"), signal.get("entityType"), signal.get("entityId"), signal.get("storeId"), signal.get("signalType"), signal.get("signalStrength"), status, signal.get("sourceRef") or f"product_signal_package:{signal.get('dataVersion') or 'latest'}", dumps(payload), created_at, now),
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
        rows = conn.execute(f"SELECT * FROM signal_pool_v14 {where} ORDER BY created_at ASC LIMIT ?", [*params, limit]).fetchall()
    items = [row_to_signal(row) for row in rows]
    by_type: Dict[str, int] = defaultdict(int)
    by_status: Dict[str, int] = defaultdict(int)
    for item in items:
        by_type[str(item.get("signalType"))] += 1
        by_status[str(item.get("status"))] += 1
    return {"version": SIGNAL_POOL_VERSION, "dataVersion": data_version, "signalCount": len(items), "byType": dict(by_type), "byStatus": dict(by_status), "signals": items}


def _normalize_snapshot_signal(signal: Dict[str, Any], source_ref: str) -> Dict[str, Any]:
    return {**signal, "version": SIGNAL_POOL_VERSION, "sourceRef": source_ref, "status": signal.get("status") or "pending_rag_agent", "rule": "V14.3 signal_pool consumes full product_signal_packages; Agent decides task value."}


def generate_signal_pool(data_version: str | None = None, *, max_signals: int = 200, user_id: str | None = None) -> Dict[str, Any]:
    ensure_signal_pool_tables()
    signal_snapshot = materialize_product_signal_snapshot(data_version=data_version, user_id=user_id, force=True)
    source_ref = signal_snapshot.get("productSignalSnapshotRef") or signal_snapshot.get("outputRef") or f"product_signal_snapshot:{data_version or 'latest'}"
    raw_signals = signal_snapshot.get("productSignalPackages") or signal_snapshot.get("signals") or []
    strength_rank = {"high": 0, "medium": 1, "low": 2, "normal": 3}
    raw_signals.sort(key=lambda item: (strength_rank.get(str(item.get("signalStrength")), 9), item.get("entityId") or "", item.get("metricCode") or ""))
    saved = [_save_signal(_normalize_snapshot_signal(signal, source_ref)) for signal in raw_signals[:max_signals]]
    by_type: Dict[str, int] = defaultdict(int)
    by_strength: Dict[str, int] = defaultdict(int)
    by_status: Dict[str, int] = defaultdict(int)
    for signal in saved:
        by_type[str(signal.get("signalType"))] += 1
        by_strength[str(signal.get("signalStrength"))] += 1
        by_status[str(signal.get("status"))] += 1
    ref = f"signal_pool:{data_version or 'latest'}"
    return {"version": SIGNAL_POOL_VERSION, "mode": "full_product_signal_package_pool_no_task_creation", "dataVersion": data_version, "productSnapshotCount": signal_snapshot.get("productSnapshotCount", 0), "productSignalPackageCount": signal_snapshot.get("productSignalPackageCount", signal_snapshot.get("productSignalCount", 0)), "productSignalCount": signal_snapshot.get("productSignalCount", 0), "taskSignalRef": ref, "outputRef": ref, "signalCount": len(saved), "createdTaskCount": 0, "byType": dict(by_type), "byStrength": dict(by_strength), "byStatus": dict(by_status), "signals": saved, "productSignalSnapshot": signal_snapshot, "rule": "V14.3 task_signal_station queues full signal packages; it does not decide operation value."}
