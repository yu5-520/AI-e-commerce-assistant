"""SQLite repository for product MVP persistence.

The repository is intentionally lightweight and stdlib-only. JSONL logs remain
as a readable audit trail, while SQLite provides queryable state for the product.
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
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def dumps(payload: Optional[Dict[str, Any]]) -> str:
    return json.dumps(payload or {}, ensure_ascii=False)


def loads(value: str | None) -> Dict[str, Any]:
    if not value:
        return {}
    return json.loads(value)


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
                auto_execution_allowed INTEGER,
                payload TEXT,
                updated_at TEXT
            )
            """
        )
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
        conn.execute("CREATE INDEX IF NOT EXISTS idx_workflow_runs_time ON workflow_runs(finished_at, started_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_execution_logs_run ON execution_logs(workflow_run_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_import_records_time ON import_records(created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_approval_records_task ON approval_records(task_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_task_status_status ON task_status(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_report_records_time ON report_records(created_at)")
        conn.commit()


def upsert_workflow_run(run: Dict[str, Any]) -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO workflow_runs (
                workflow_run_id,
                workflow_type,
                status,
                input_snapshot,
                output_snapshot,
                started_at,
                finished_at,
                error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(workflow_run_id) DO UPDATE SET
                workflow_type=excluded.workflow_type,
                status=excluded.status,
                input_snapshot=COALESCE(excluded.input_snapshot, workflow_runs.input_snapshot),
                output_snapshot=COALESCE(excluded.output_snapshot, workflow_runs.output_snapshot),
                started_at=COALESCE(workflow_runs.started_at, excluded.started_at),
                finished_at=COALESCE(excluded.finished_at, workflow_runs.finished_at),
                error_message=COALESCE(excluded.error_message, workflow_runs.error_message)
            """,
            (
                run.get("workflow_run_id"),
                run.get("workflow_type"),
                run.get("status"),
                dumps(run.get("input_snapshot")) if "input_snapshot" in run else None,
                dumps(run.get("output_snapshot")) if "output_snapshot" in run else None,
                run.get("started_at"),
                run.get("finished_at"),
                run.get("error_message"),
            ),
        )
        conn.commit()


def insert_execution_log(log: Dict[str, Any]) -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO execution_logs (
                log_id,
                workflow_run_id,
                node_name,
                status,
                input_snapshot,
                output_snapshot,
                error_message,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log.get("log_id"),
                log.get("workflow_run_id"),
                log.get("node_name"),
                log.get("status"),
                dumps(log.get("input_snapshot")),
                dumps(log.get("output_snapshot")),
                log.get("error_message"),
                log.get("created_at"),
            ),
        )
        conn.commit()


def insert_import_record(record: Dict[str, Any]) -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO import_records (
                import_id,
                workflow_run_id,
                mode,
                status,
                dataset_count,
                total_rows,
                validation,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.get("import_id"),
                record.get("workflow_run_id"),
                record.get("mode"),
                record.get("status"),
                record.get("dataset_count"),
                record.get("total_rows"),
                dumps(record.get("validation")),
                record.get("created_at"),
            ),
        )
        conn.commit()


def insert_approval_record(record: Dict[str, Any]) -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO approval_records (
                approval_id,
                workflow_run_id,
                task_id,
                approval_status,
                operator,
                risk_level,
                task_type,
                payload,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.get("approval_id"),
                record.get("workflow_run_id"),
                record.get("task_id"),
                record.get("approval_status"),
                record.get("operator"),
                record.get("risk_level"),
                record.get("task_type"),
                dumps(record),
                record.get("updated_at") or record.get("created_at"),
            ),
        )
        conn.commit()


def upsert_task_status(task: Dict[str, Any]) -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO task_status (
                task_id,
                workflow_run_id,
                task_type,
                risk_level,
                approval_status,
                status,
                auto_execution_allowed,
                payload,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(task_id) DO UPDATE SET
                workflow_run_id=excluded.workflow_run_id,
                task_type=excluded.task_type,
                risk_level=excluded.risk_level,
                approval_status=excluded.approval_status,
                status=excluded.status,
                auto_execution_allowed=excluded.auto_execution_allowed,
                payload=excluded.payload,
                updated_at=excluded.updated_at
            """,
            (
                task.get("task_id"),
                task.get("workflow_run_id"),
                task.get("task_type"),
                task.get("risk_level"),
                task.get("approval_status"),
                task.get("status"),
                1 if task.get("auto_execution_allowed") is True else 0,
                dumps(task),
                task.get("updated_at"),
            ),
        )
        conn.commit()


def insert_report_record(record: Dict[str, Any]) -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO report_records (
                report_id,
                workflow_run_id,
                report_type,
                path,
                format,
                payload,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.get("report_id"),
                record.get("workflow_run_id"),
                record.get("report_type"),
                record.get("path"),
                record.get("format"),
                dumps(record),
                record.get("created_at"),
            ),
        )
        conn.commit()


def row_to_workflow_run(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "workflow_run_id": row["workflow_run_id"],
        "workflow_type": row["workflow_type"],
        "status": row["status"],
        "input_snapshot": loads(row["input_snapshot"]),
        "output_snapshot": loads(row["output_snapshot"]),
        "started_at": row["started_at"],
        "finished_at": row["finished_at"],
        "error_message": row["error_message"],
    }


def row_to_execution_log(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "log_id": row["log_id"],
        "workflow_run_id": row["workflow_run_id"],
        "node_name": row["node_name"],
        "status": row["status"],
        "input_snapshot": loads(row["input_snapshot"]),
        "output_snapshot": loads(row["output_snapshot"]),
        "error_message": row["error_message"],
        "created_at": row["created_at"],
    }


def row_to_import_record(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "import_id": row["import_id"],
        "workflow_run_id": row["workflow_run_id"],
        "mode": row["mode"],
        "status": row["status"],
        "dataset_count": row["dataset_count"],
        "total_rows": row["total_rows"],
        "validation": loads(row["validation"]),
        "created_at": row["created_at"],
    }


def row_to_approval_record(row: sqlite3.Row) -> Dict[str, Any]:
    payload = loads(row["payload"])
    return {
        **payload,
        "approval_id": row["approval_id"],
        "workflow_run_id": row["workflow_run_id"],
        "task_id": row["task_id"],
        "approval_status": row["approval_status"],
        "operator": row["operator"],
        "risk_level": row["risk_level"],
        "task_type": row["task_type"],
        "created_at": row["created_at"],
    }


def row_to_task_status(row: sqlite3.Row) -> Dict[str, Any]:
    payload = loads(row["payload"])
    return {
        **payload,
        "task_id": row["task_id"],
        "workflow_run_id": row["workflow_run_id"],
        "task_type": row["task_type"],
        "risk_level": row["risk_level"],
        "approval_status": row["approval_status"],
        "status": row["status"],
        "auto_execution_allowed": bool(row["auto_execution_allowed"]),
        "updated_at": row["updated_at"],
    }


def row_to_report_record(row: sqlite3.Row) -> Dict[str, Any]:
    payload = loads(row["payload"])
    return {
        **payload,
        "report_id": row["report_id"],
        "workflow_run_id": row["workflow_run_id"],
        "report_type": row["report_type"],
        "path": row["path"],
        "format": row["format"],
        "created_at": row["created_at"],
    }


def list_workflow_runs(limit: int = 50) -> List[Dict[str, Any]]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM workflow_runs
            ORDER BY COALESCE(finished_at, started_at) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [row_to_workflow_run(row) for row in rows]


def list_execution_logs(limit: int = 100) -> List[Dict[str, Any]]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM execution_logs
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [row_to_execution_log(row) for row in rows]


def list_execution_logs_by_run(workflow_run_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM execution_logs
            WHERE workflow_run_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (workflow_run_id, limit),
        ).fetchall()
    return [row_to_execution_log(row) for row in rows]


def list_import_records(limit: int = 20) -> List[Dict[str, Any]]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM import_records
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [row_to_import_record(row) for row in rows]


def list_approval_records(limit: int = 50) -> List[Dict[str, Any]]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM approval_records
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [row_to_approval_record(row) for row in rows]


def list_task_status(limit: int = 100) -> List[Dict[str, Any]]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM task_status
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [row_to_task_status(row) for row in rows]


def get_task_status_map() -> Dict[str, Dict[str, Any]]:
    return {item["task_id"]: item for item in list_task_status(limit=1000)}


def list_report_records(limit: int = 50) -> List[Dict[str, Any]]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM report_records
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [row_to_report_record(row) for row in rows]
