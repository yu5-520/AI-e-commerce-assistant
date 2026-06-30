"""SQLite repository for product MVP persistence.

V14.8 enables WAL and a short busy timeout so frontend read-model SELECT calls do
not get unnecessarily blocked while the worker writes station/task results.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT_DIR / "logs"
DB_PATH = LOG_DIR / "product_workbench.sqlite3"


def connect() -> sqlite3.Connection:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=3.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=3000")
        conn.execute("PRAGMA synchronous=NORMAL")
    except Exception:
        pass
    return conn


def dumps(payload: Optional[Dict[str, Any]]) -> str:
    return json.dumps(payload or {}, ensure_ascii=False)


def loads(value: str | None) -> Dict[str, Any]:
    if not value:
        return {}
    return json.loads(value)


def ensure_columns(conn: sqlite3.Connection, table_name: str, columns: Dict[str, str]) -> None:
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}
    for name, definition in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {name} {definition}")


def init_db() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS workflow_runs (
                workflow_run_id TEXT PRIMARY KEY,
                workflow_type TEXT NOT NULL,
                status TEXT NOT NULL,
                input_snapshot TEXT,
                output_snapshot TEXT,
                started_at TEXT,
                finished_at TEXT,
                error_message TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS execution_logs (
                log_id TEXT PRIMARY KEY,
                workflow_run_id TEXT NOT NULL,
                node_name TEXT NOT NULL,
                status TEXT NOT NULL,
                input_snapshot TEXT,
                output_snapshot TEXT,
                error_message TEXT,
                created_at TEXT,
                FOREIGN KEY(workflow_run_id) REFERENCES workflow_runs(workflow_run_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS import_records (
                import_id TEXT PRIMARY KEY,
                workflow_run_id TEXT,
                mode TEXT NOT NULL,
                status TEXT NOT NULL,
                dataset_count INTEGER,
                total_rows INTEGER,
                validation TEXT,
                created_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS approval_records (
                approval_id TEXT PRIMARY KEY,
                workflow_run_id TEXT,
                task_id TEXT NOT NULL,
                approval_status TEXT NOT NULL,
                operator TEXT,
                risk_level TEXT,
                task_type TEXT,
                payload TEXT,
                created_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS task_status (
                task_id TEXT PRIMARY KEY,
                workflow_run_id TEXT,
                task_type TEXT,
                risk_level TEXT,
                approval_status TEXT,
                status TEXT,
                workflow_status TEXT,
                assignee_id TEXT,
                reviewer_id TEXT,
                auto_execution_allowed INTEGER,
                payload TEXT,
                updated_at TEXT
            )
            """
        )
        ensure_columns(conn, "task_status", {"workflow_status": "TEXT", "assignee_id": "TEXT", "reviewer_id": "TEXT"})
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS report_records (
                report_id TEXT PRIMARY KEY,
                workflow_run_id TEXT,
                report_type TEXT NOT NULL,
                path TEXT,
                format TEXT,
                payload TEXT,
                created_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                user_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                role_id TEXT NOT NULL,
                status TEXT NOT NULL,
                payload TEXT,
                updated_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS roles (
                role_id TEXT PRIMARY KEY,
                role_name TEXT NOT NULL,
                payload TEXT,
                updated_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS store_permissions (
                permission_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                store_id TEXT NOT NULL,
                permission_level TEXT NOT NULL,
                payload TEXT,
                updated_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS product_permissions (
                permission_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                store_id TEXT,
                permission_level TEXT NOT NULL,
                payload TEXT,
                updated_at TEXT
            )
            """
        )
        conn.commit()
