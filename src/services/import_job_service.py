"""P0 ImportJob / ProjectionJob runtime scaffold.

This service wraps report imports with durable job records without removing the
existing demo import implementation. It is the bridge toward ImportJob ->
DataVersion -> ImportedRows -> ProjectionJob -> AlertEvent -> TaskDraft.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List
from uuid import uuid4

from src.core.context import UserContext
from src.repositories.sqlite_repository import connect, dumps, init_db, loads
from src.services.report_task_repository_sync_service import sync_report_tasks
from src.services.task_state_machine_service import task_persistence_summary

IMPORT_JOB_VERSION = "5.1.9"


def _job_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}".upper()


def ensure_import_job_tables() -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS import_jobs (
                import_job_id TEXT PRIMARY KEY,
                tenant_id TEXT DEFAULT 'tenant_demo',
                org_id TEXT DEFAULT 'org_demo',
                dataset_name TEXT,
                source_type TEXT,
                status TEXT NOT NULL,
                row_count INTEGER DEFAULT 0,
                alert_count INTEGER DEFAULT 0,
                task_count INTEGER DEFAULT 0,
                data_version TEXT,
                input_snapshot TEXT,
                output_snapshot TEXT,
                error_message TEXT,
                created_by TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                deleted_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS projection_jobs (
                projection_job_id TEXT PRIMARY KEY,
                import_job_id TEXT NOT NULL,
                tenant_id TEXT DEFAULT 'tenant_demo',
                org_id TEXT DEFAULT 'org_demo',
                projection_type TEXT NOT NULL,
                status TEXT NOT NULL,
                input_snapshot TEXT,
                output_snapshot TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                deleted_at TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_import_jobs_tenant_time ON import_jobs(tenant_id, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_projection_jobs_import ON projection_jobs(import_job_id, created_at)")
        conn.commit()


def _now_expr() -> str:
    return "datetime('now')"


def _insert_import_job(ctx: UserContext, *, dataset_name: str, source_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    ensure_import_job_tables()
    job_id = _job_id("IMPORTJOB")
    with connect() as conn:
        conn.execute(
            f"""
            INSERT INTO import_jobs (
                import_job_id, tenant_id, org_id, dataset_name, source_type,
                status, row_count, input_snapshot, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'running', ?, ?, ?, {_now_expr()}, {_now_expr()})
            """,
            (job_id, ctx.tenant_id, ctx.org_id, dataset_name, source_type, len(payload.get("rows") or []), dumps(payload), ctx.user_id),
        )
        conn.commit()
    return {"importJobId": job_id, "status": "running", "datasetName": dataset_name, "sourceType": source_type}


def _update_import_job(ctx: UserContext, job_id: str, *, status: str, result: Dict[str, Any] | None = None, error: str | None = None) -> None:
    result = result or {}
    with connect() as conn:
        conn.execute(
            f"""
            UPDATE import_jobs
            SET status = ?, row_count = ?, alert_count = ?, task_count = ?, data_version = ?,
                output_snapshot = ?, error_message = ?, updated_at = {_now_expr()}
            WHERE import_job_id = ? AND tenant_id = ? AND deleted_at IS NULL
            """,
            (
                status,
                result.get("rowCount") or result.get("totalRows") or len(result.get("rows") or []),
                result.get("alertCount") or result.get("activeAlertCount") or len(result.get("alerts") or []),
                result.get("createdTaskCount") or result.get("taskCount") or len(result.get("tasks") or []),
                result.get("dataVersion") or result.get("version"),
                dumps(result),
                error,
                job_id,
                ctx.tenant_id,
            ),
        )
        conn.commit()


def _insert_projection_job(ctx: UserContext, job_id: str, projection_type: str, result: Dict[str, Any]) -> Dict[str, Any]:
    projection_job_id = _job_id("PROJECTIONJOB")
    status = "completed" if not result.get("error") else "failed"
    with connect() as conn:
        conn.execute(
            f"""
            INSERT INTO projection_jobs (
                projection_job_id, import_job_id, tenant_id, org_id, projection_type,
                status, input_snapshot, output_snapshot, error_message, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, {_now_expr()}, {_now_expr()})
            """,
            (projection_job_id, job_id, ctx.tenant_id, ctx.org_id, projection_type, status, dumps({"importJobId": job_id}), dumps(result), result.get("error")),
        )
        conn.commit()
    return {"projectionJobId": projection_job_id, "projectionType": projection_type, "status": status}


def run_import_job(
    ctx: UserContext,
    *,
    dataset_name: str,
    source_type: str,
    payload: Dict[str, Any],
    runner: Callable[[], Dict[str, Any]],
) -> Dict[str, Any]:
    """Create an ImportJob, run existing import logic, then persist projection sync."""

    job = _insert_import_job(ctx, dataset_name=dataset_name, source_type=source_type, payload=payload)
    try:
        result = runner()
        synced_result = sync_report_tasks(result, ctx)
        task_sync = synced_result.get("taskRepositorySync") or {}
        projections = [
            _insert_projection_job(ctx, job["importJobId"], "module_projection_refresh", synced_result),
            _insert_projection_job(ctx, job["importJobId"], "alert_task_repository_sync", task_sync),
        ]
        _update_import_job(ctx, job["importJobId"], status="completed", result=synced_result)
        return {
            "version": IMPORT_JOB_VERSION,
            "importJob": {**job, "status": "completed"},
            "projectionJobs": projections,
            "result": synced_result,
            "taskPersistence": task_persistence_summary(),
            "rule": "现有导入逻辑保持不变；ImportJob 负责记录导入、投影和任务同步链路。",
        }
    except Exception as exc:  # noqa: BLE001 - API layer converts to HTTP error.
        _update_import_job(ctx, job["importJobId"], status="failed", error=str(exc))
        _insert_projection_job(ctx, job["importJobId"], "import_failed", {"error": str(exc)})
        raise


def _row_to_import_job(row: Any) -> Dict[str, Any]:
    return {
        "importJobId": row["import_job_id"],
        "tenantId": row["tenant_id"],
        "orgId": row["org_id"],
        "datasetName": row["dataset_name"],
        "sourceType": row["source_type"],
        "status": row["status"],
        "rowCount": row["row_count"],
        "alertCount": row["alert_count"],
        "taskCount": row["task_count"],
        "dataVersion": row["data_version"],
        "inputSnapshot": loads(row["input_snapshot"]),
        "outputSnapshot": loads(row["output_snapshot"]),
        "errorMessage": row["error_message"],
        "createdBy": row["created_by"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def _row_to_projection_job(row: Any) -> Dict[str, Any]:
    return {
        "projectionJobId": row["projection_job_id"],
        "importJobId": row["import_job_id"],
        "tenantId": row["tenant_id"],
        "orgId": row["org_id"],
        "projectionType": row["projection_type"],
        "status": row["status"],
        "inputSnapshot": loads(row["input_snapshot"]),
        "outputSnapshot": loads(row["output_snapshot"]),
        "errorMessage": row["error_message"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def list_import_jobs(ctx: UserContext, limit: int = 50) -> Dict[str, Any]:
    ensure_import_job_tables()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM import_jobs
            WHERE tenant_id = ? AND deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (ctx.tenant_id, limit),
        ).fetchall()
    jobs = [_row_to_import_job(row) for row in rows]
    return {"version": IMPORT_JOB_VERSION, "count": len(jobs), "jobs": jobs}


def get_import_job(ctx: UserContext, import_job_id: str) -> Dict[str, Any] | None:
    ensure_import_job_tables()
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM import_jobs WHERE import_job_id = ? AND tenant_id = ? AND deleted_at IS NULL",
            (import_job_id, ctx.tenant_id),
        ).fetchone()
        if not row:
            return None
        projection_rows = conn.execute(
            "SELECT * FROM projection_jobs WHERE import_job_id = ? AND tenant_id = ? AND deleted_at IS NULL ORDER BY created_at ASC",
            (import_job_id, ctx.tenant_id),
        ).fetchall()
    return {"version": IMPORT_JOB_VERSION, "job": _row_to_import_job(row), "projectionJobs": [_row_to_projection_job(item) for item in projection_rows]}
