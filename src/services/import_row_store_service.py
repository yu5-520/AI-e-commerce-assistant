"""Persist full imported report rows for V5 module projection."""

from __future__ import annotations

from sqlite3 import OperationalError
from typing import Any, Dict, List

from src.repositories.sqlite_repository import connect, dumps, loads
from src.services.report_alert_service import now_iso


def ensure_import_row_table() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS imported_report_rows (
                row_id TEXT PRIMARY KEY,
                data_version TEXT NOT NULL,
                dataset_name TEXT NOT NULL,
                row_index INTEGER NOT NULL,
                store_id TEXT,
                payload TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_imported_rows_version ON imported_report_rows(data_version, row_index)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_imported_rows_dataset ON imported_report_rows(dataset_name, data_version)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_imported_rows_store ON imported_report_rows(store_id)")
        conn.commit()


def _store_id(row: Dict[str, Any]) -> str | None:
    for key in ["store_id", "storeId", "店铺ID", "店铺id", "店铺编号", "店铺编码"]:
        value = row.get(key)
        if value not in {None, ""}:
            return str(value)
    return None


def save_import_rows(data_version: str, dataset_name: str, rows: List[Dict[str, Any]]) -> None:
    ensure_import_row_table()
    created_at = now_iso()
    with connect() as conn:
        conn.execute("DELETE FROM imported_report_rows WHERE data_version = ?", (data_version,))
        for index, row in enumerate(rows):
            payload = {str(key): value for key, value in row.items()}
            payload.setdefault("dataVersion", data_version)
            payload.setdefault("datasetName", dataset_name)
            conn.execute(
                """
                INSERT OR REPLACE INTO imported_report_rows (
                    row_id, data_version, dataset_name, row_index, store_id, payload, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (f"{data_version}:{index}", data_version, dataset_name, index, _store_id(payload), dumps(payload), created_at),
            )
        conn.commit()


def load_import_rows(dataset_name: str | None = None) -> List[Dict[str, Any]]:
    try:
        ensure_import_row_table()
        query = "SELECT * FROM imported_report_rows"
        params: List[Any] = []
        if dataset_name:
            query += " WHERE dataset_name = ?"
            params.append(dataset_name)
        query += " ORDER BY data_version ASC, row_index ASC"
        with connect() as conn:
            rows = conn.execute(query, params).fetchall()
    except OperationalError:
        return []
    result: List[Dict[str, Any]] = []
    for row in rows:
        payload = loads(row["payload"])
        if payload:
            payload.setdefault("dataVersion", row["data_version"])
            payload.setdefault("datasetName", row["dataset_name"])
            if row["store_id"] and not payload.get("storeId"):
                payload["storeId"] = row["store_id"]
            result.append(payload)
    return result
