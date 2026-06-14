"""System status service for the product workbench."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from src.repositories.sqlite_repository import DB_PATH, connect, init_db

TABLES = [
    {
        "table_name": "workflow_runs",
        "time_expression": "COALESCE(MAX(finished_at), MAX(started_at))",
    },
    {
        "table_name": "execution_logs",
        "time_expression": "MAX(created_at)",
    },
    {
        "table_name": "import_records",
        "time_expression": "MAX(created_at)",
    },
    {
        "table_name": "approval_records",
        "time_expression": "MAX(created_at)",
    },
    {
        "table_name": "task_status",
        "time_expression": "MAX(updated_at)",
    },
    {
        "table_name": "report_records",
        "time_expression": "MAX(created_at)",
    },
]


def get_table_status(table_name: str, time_expression: str) -> Dict[str, Any]:
    with connect() as conn:
        count_row = conn.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
        latest_row = conn.execute(f"SELECT {time_expression} AS latest_at FROM {table_name}").fetchone()
    return {
        "table_name": table_name,
        "record_count": int(count_row["count"] if count_row else 0),
        "latest_at": latest_row["latest_at"] if latest_row else None,
    }


def get_db_status() -> Dict[str, Any]:
    """Return SQLite database status for health checks and UI display."""
    init_db()
    db_path = Path(DB_PATH)
    table_status: List[Dict[str, Any]] = [
        get_table_status(item["table_name"], item["time_expression"]) for item in TABLES
    ]
    total_records = sum(item["record_count"] for item in table_status)
    latest_times = [item["latest_at"] for item in table_status if item.get("latest_at")]
    return {
        "ok": True,
        "database": {
            "type": "sqlite",
            "path": str(db_path),
            "exists": db_path.exists(),
            "size_bytes": db_path.stat().st_size if db_path.exists() else 0,
        },
        "tables": table_status,
        "summary": {
            "table_count": len(table_status),
            "total_records": total_records,
            "latest_at": max(latest_times) if latest_times else None,
        },
        "runtime_boundary": {
            "real_erp_connected": False,
            "real_crm_connected": False,
            "real_shop_backend_connected": False,
            "auto_high_risk_execution": False,
        },
    }
