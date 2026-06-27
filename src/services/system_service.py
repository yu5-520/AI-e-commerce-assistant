"""System status and runtime reset service for the product workbench."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from src.repositories.sqlite_repository import DB_PATH, connect, init_db
from src.services.module_task_service import reset_tasks

ROOT_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT_DIR / "logs"
JSONL_LOG_FILES = [
    LOG_DIR / "workflow_runs.jsonl",
    LOG_DIR / "execution_logs.jsonl",
    LOG_DIR / "data_import_records.jsonl",
    LOG_DIR / "approval_records.jsonl",
]

V5_RUNTIME_RESET_MARKER = "v5_0_3_runtime_empty_state_applied"
V1114_RUNTIME_RESET_MARKER = "v11_14_runtime_full_demo_reset_applied"
V121_RUNTIME_RESET_MARKER = "v12_1_metric_fact_runtime_reset_applied"
V1213_RUNTIME_RESET_MARKER = "v12_1_3_data_gap_runtime_reset_applied"

TABLES = [
    {"table_name": "workflow_runs", "time_expression": "COALESCE(MAX(finished_at), MAX(started_at))"},
    {"table_name": "execution_logs", "time_expression": "MAX(created_at)"},
    {"table_name": "import_records", "time_expression": "MAX(created_at)"},
    {"table_name": "approval_records", "time_expression": "MAX(created_at)"},
    {"table_name": "task_status", "time_expression": "MAX(updated_at)"},
    {"table_name": "task_assignments", "time_expression": "MAX(created_at)"},
    {"table_name": "task_submissions", "time_expression": "MAX(created_at)"},
    {"table_name": "task_reviews", "time_expression": "MAX(created_at)"},
    {"table_name": "report_records", "time_expression": "MAX(created_at)"},
    {"table_name": "data_snapshots", "time_expression": "MAX(created_at)"},
    {"table_name": "metric_snapshots", "time_expression": "MAX(created_at)"},
    {"table_name": "business_signals_v6", "time_expression": "MAX(created_at)"},
    {"table_name": "alert_events", "time_expression": "MAX(updated_at)"},
    {"table_name": "imported_report_rows", "time_expression": "MAX(created_at)"},
    {"table_name": "operating_products", "time_expression": "MAX(updated_at)"},
    {"table_name": "operating_stores", "time_expression": "MAX(updated_at)"},
    {"table_name": "product_metric_facts", "time_expression": "MAX(updated_at)"},
    {"table_name": "store_metric_facts", "time_expression": "MAX(updated_at)"},
    {"table_name": "traffic_source_facts", "time_expression": "MAX(updated_at)"},
    {"table_name": "data_gap_events", "time_expression": "MAX(updated_at)"},
]

# Demo reset must remove the whole import-derived graph, not only raw report rows.
# Keep seed/security tables such as accounts, roles, stores, memberships and runtime_meta.
RUNTIME_TABLES = [
    "task_reviews",
    "task_submissions",
    "task_assignments",
    "approval_records",
    "task_status",
    "alert_events",
    "business_signals_v6",
    "metric_snapshots",
    "product_metric_facts",
    "store_metric_facts",
    "traffic_source_facts",
    "data_gap_events",
    "data_snapshots",
    "imported_report_rows",
    "report_records",
    "import_records",
    "execution_logs",
    "workflow_runs",
    "operating_products",
    "operating_stores",
]


RUNTIME_BOUNDARY_NOTE = "清空演示环境会删除报表导入、快照、业务信号、任务、日志、导入生成的经营对象主档、指标事实和数据缺口；账号、角色、权限和基础店铺配置保留。"


def _table_exists(conn, table_name: str) -> bool:
    row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone()
    return bool(row)


def _ensure_runtime_meta(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS runtime_meta (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _meta_get(conn, key: str) -> str | None:
    _ensure_runtime_meta(conn)
    row = conn.execute("SELECT value FROM runtime_meta WHERE key=?", (key,)).fetchone()
    return row["value"] if row else None


def _meta_set(conn, key: str, value: str) -> None:
    _ensure_runtime_meta(conn)
    conn.execute(
        "INSERT OR REPLACE INTO runtime_meta(key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
        (key, value),
    )


def _table_count(conn, table_name: str) -> int:
    if not _table_exists(conn, table_name):
        return 0
    row = conn.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
    return int(row["count"] if row else 0)


def _delete_runtime_tables(conn) -> Dict[str, int]:
    deleted: Dict[str, int] = {}
    for table_name in RUNTIME_TABLES:
        if not _table_exists(conn, table_name):
            deleted[table_name] = 0
            continue
        count = _table_count(conn, table_name)
        conn.execute(f"DELETE FROM {table_name}")
        deleted[table_name] = count
    return deleted


def get_table_status(table_name: str, time_expression: str) -> Dict[str, Any]:
    with connect() as conn:
        if not _table_exists(conn, table_name):
            return {"table_name": table_name, "record_count": 0, "latest_at": None, "exists": False}
        count_row = conn.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
        try:
            latest_row = conn.execute(f"SELECT {time_expression} AS latest_at FROM {table_name}").fetchone()
        except Exception:
            latest_row = None
    return {
        "table_name": table_name,
        "record_count": int(count_row["count"] if count_row else 0),
        "latest_at": latest_row["latest_at"] if latest_row else None,
        "exists": True,
    }


def get_db_status() -> Dict[str, Any]:
    """Return SQLite database status for health checks and UI display."""
    init_db()
    db_path = Path(DB_PATH)
    table_status: List[Dict[str, Any]] = [get_table_status(item["table_name"], item["time_expression"]) for item in TABLES]
    total_records = sum(item["record_count"] for item in table_status)
    latest_times = [item["latest_at"] for item in table_status if item.get("latest_at")]
    with connect() as conn:
        reset_marker = _meta_get(conn, V5_RUNTIME_RESET_MARKER)
        full_reset_marker = _meta_get(conn, V1114_RUNTIME_RESET_MARKER)
        metric_fact_reset_marker = _meta_get(conn, V121_RUNTIME_RESET_MARKER)
        data_gap_reset_marker = _meta_get(conn, V1213_RUNTIME_RESET_MARKER)
    return {
        "ok": True,
        "database": {"type": "sqlite", "path": str(db_path), "exists": db_path.exists(), "size_bytes": db_path.stat().st_size if db_path.exists() else 0},
        "tables": table_status,
        "summary": {"table_count": len(table_status), "total_records": total_records, "latest_at": max(latest_times) if latest_times else None},
        "runtime_boundary": {"real_erp_connected": False, "real_crm_connected": False, "real_shop_backend_connected": False, "auto_high_risk_execution": False, "note": RUNTIME_BOUNDARY_NOTE},
        "v5RuntimeReset": {"marker": V5_RUNTIME_RESET_MARKER, "applied": reset_marker == "done"},
        "v1114RuntimeFullReset": {"marker": V1114_RUNTIME_RESET_MARKER, "applied": full_reset_marker == "done"},
        "v121MetricFactRuntimeReset": {"marker": V121_RUNTIME_RESET_MARKER, "applied": metric_fact_reset_marker == "done"},
        "v1213DataGapRuntimeReset": {"marker": V1213_RUNTIME_RESET_MARKER, "applied": data_gap_reset_marker == "done"},
    }


def clear_runtime_data(include_audit_logs: bool = True, *, reason: str = "manual_reset") -> Dict[str, Any]:
    """Clear generated runtime data while keeping product code and account seed boundaries."""
    init_db()
    removed_files: List[str] = []
    with connect() as conn:
        deleted_tables = _delete_runtime_tables(conn)
        _meta_set(conn, V5_RUNTIME_RESET_MARKER, "done")
        _meta_set(conn, f"{V5_RUNTIME_RESET_MARKER}_reason", reason)
        _meta_set(conn, V1114_RUNTIME_RESET_MARKER, "done")
        _meta_set(conn, f"{V1114_RUNTIME_RESET_MARKER}_reason", reason)
        _meta_set(conn, V121_RUNTIME_RESET_MARKER, "done")
        _meta_set(conn, f"{V121_RUNTIME_RESET_MARKER}_reason", reason)
        _meta_set(conn, V1213_RUNTIME_RESET_MARKER, "done")
        _meta_set(conn, f"{V1213_RUNTIME_RESET_MARKER}_reason", reason)
        conn.commit()

    reset_tasks()

    if include_audit_logs:
        for path in JSONL_LOG_FILES:
            if path.exists():
                path.unlink()
                removed_files.append(str(path))

    return {
        "ok": True,
        "message": "演示运行态已全链路清空：导入行、快照、业务信号、任务、日志、经营商品、经营店铺、指标事实和数据缺口均回到空状态。",
        "reason": reason,
        "deletedTables": deleted_tables,
        "removedFiles": removed_files,
        "includeAuditLogs": include_audit_logs,
        "boundary": RUNTIME_BOUNDARY_NOTE,
        "db_status": get_db_status(),
    }


def clear_demo_data(include_audit_logs: bool = True) -> Dict[str, Any]:
    """Backward-compatible alias for clearing generated runtime data."""
    return clear_runtime_data(include_audit_logs=include_audit_logs, reason="clear_demo_data_alias")


def reset_legacy_runtime_once() -> Dict[str, Any]:
    """Apply one-time empty-state cleanup after the V5 no-fallback migration.

    This solves the deployment case where old SQLite report snapshots still feed
    ModuleProjection after the frontend fallback content has been removed.
    """
    init_db()
    with connect() as conn:
        if _meta_get(conn, V1213_RUNTIME_RESET_MARKER) == "done" or _meta_get(conn, V121_RUNTIME_RESET_MARKER) == "done" or _meta_get(conn, V1114_RUNTIME_RESET_MARKER) == "done" or _meta_get(conn, V5_RUNTIME_RESET_MARKER) == "done":
            return {"ok": True, "skipped": True, "marker": V1213_RUNTIME_RESET_MARKER, "message": "Runtime cleanup already applied."}
        stale_count = sum(_table_count(conn, table_name) for table_name in RUNTIME_TABLES)
    if stale_count <= 0:
        with connect() as conn:
            _meta_set(conn, V5_RUNTIME_RESET_MARKER, "done")
            _meta_set(conn, f"{V5_RUNTIME_RESET_MARKER}_reason", "empty_runtime_noop")
            _meta_set(conn, V1114_RUNTIME_RESET_MARKER, "done")
            _meta_set(conn, f"{V1114_RUNTIME_RESET_MARKER}_reason", "empty_runtime_noop")
            _meta_set(conn, V121_RUNTIME_RESET_MARKER, "done")
            _meta_set(conn, f"{V121_RUNTIME_RESET_MARKER}_reason", "empty_runtime_noop")
            _meta_set(conn, V1213_RUNTIME_RESET_MARKER, "done")
            _meta_set(conn, f"{V1213_RUNTIME_RESET_MARKER}_reason", "empty_runtime_noop")
            conn.commit()
        reset_tasks()
        return {"ok": True, "skipped": True, "marker": V1213_RUNTIME_RESET_MARKER, "staleRecordCount": 0, "message": "Runtime already empty; cleanup marker recorded."}
    result = clear_runtime_data(include_audit_logs=False, reason="v1213_startup_one_time_full_runtime_cleanup")
    result["staleRecordCount"] = stale_count
    result["marker"] = V1213_RUNTIME_RESET_MARKER
    return result
