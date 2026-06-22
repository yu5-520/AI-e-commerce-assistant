"""Worker / Redis queue scaffold with trace audit."""

from __future__ import annotations

from typing import Any, Dict
from uuid import uuid4

from src.core.context import UserContext
from src.repositories.sqlite_repository import connect, dumps, init_db, loads
from src.services.trace_audit_service import resolve_trace_id, write_audit_log

WORKER_QUEUE_VERSION = "5.2.5"
ACTIVE_STATUSES = {"queued", "claimed", "running", "retry_scheduled"}
TERMINAL_STATUSES = {"completed", "failed", "cancelled"}
SUPPORTED_JOB_TYPES = {"import_report", "projection_refresh", "alert_generation", "task_repository_sync", "agent_analysis", "rag_memory_write"}


def _worker_job_id() -> str:
    return f"WORKERJOB_{uuid4().hex[:10]}".upper()


def ensure_worker_queue_tables() -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS worker_jobs (
                worker_job_id TEXT PRIMARY KEY,
                tenant_id TEXT DEFAULT 'tenant_demo',
                org_id TEXT DEFAULT 'org_demo',
                queue_name TEXT NOT NULL,
                job_type TEXT NOT NULL,
                status TEXT NOT NULL,
                priority INTEGER DEFAULT 50,
                attempt_count INTEGER DEFAULT 0,
                max_attempts INTEGER DEFAULT 3,
                idempotency_key TEXT,
                correlation_id TEXT,
                payload TEXT,
                result TEXT,
                error_message TEXT,
                created_by TEXT,
                claimed_by TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                claimed_at TEXT,
                finished_at TEXT,
                next_run_at TEXT,
                deleted_at TEXT
            )
            """
        )
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(worker_jobs)").fetchall()}
        if "trace_id" not in columns:
            conn.execute("ALTER TABLE worker_jobs ADD COLUMN trace_id TEXT")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_worker_jobs_tenant_queue ON worker_jobs(tenant_id, queue_name, status, priority, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_worker_jobs_correlation ON worker_jobs(tenant_id, correlation_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_worker_jobs_trace ON worker_jobs(trace_id)")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_worker_jobs_idempotency ON worker_jobs(tenant_id, idempotency_key) WHERE idempotency_key IS NOT NULL AND deleted_at IS NULL")
        conn.commit()


def _now_expr() -> str:
    return "datetime('now')"


def _row_to_worker_job(row: Any) -> Dict[str, Any]:
    keys = row.keys()
    return {
        "workerJobId": row["worker_job_id"],
        "traceId": row["trace_id"] if "trace_id" in keys else None,
        "tenantId": row["tenant_id"],
        "orgId": row["org_id"],
        "queueName": row["queue_name"],
        "jobType": row["job_type"],
        "status": row["status"],
        "priority": row["priority"],
        "attemptCount": row["attempt_count"],
        "maxAttempts": row["max_attempts"],
        "idempotencyKey": row["idempotency_key"],
        "correlationId": row["correlation_id"],
        "payload": loads(row["payload"]),
        "result": loads(row["result"]),
        "errorMessage": row["error_message"],
        "createdBy": row["created_by"],
        "claimedBy": row["claimed_by"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
        "claimedAt": row["claimed_at"],
        "finishedAt": row["finished_at"],
        "nextRunAt": row["next_run_at"],
    }


def enqueue_worker_job(ctx: UserContext, payload: Dict[str, Any]) -> Dict[str, Any]:
    ensure_worker_queue_tables()
    job_type = payload.get("jobType") or payload.get("job_type") or "import_report"
    if job_type not in SUPPORTED_JOB_TYPES:
        raise ValueError(f"unsupported worker job type: {job_type}")
    queue_name = payload.get("queueName") or payload.get("queue_name") or "default"
    idempotency_key = payload.get("idempotencyKey") or payload.get("idempotency_key")
    trace_id = resolve_trace_id(payload.get("payload") or payload, "WORKERTRACE")
    job_payload = {**(payload.get("payload") or {}), "traceId": trace_id}
    with connect() as conn:
        if idempotency_key:
            existing = conn.execute("SELECT * FROM worker_jobs WHERE tenant_id = ? AND idempotency_key = ? AND deleted_at IS NULL", (ctx.tenant_id, idempotency_key)).fetchone()
            if existing:
                job = _row_to_worker_job(existing)
                write_audit_log(ctx, trace_id=job.get("traceId") or trace_id, event_type="worker_job.idempotent_reused", resource_type="worker_job", resource_id=job.get("workerJobId"), action=job_type, status=job.get("status"), payload={"idempotencyKey": idempotency_key})
                return {"version": WORKER_QUEUE_VERSION, "created": False, "job": job}
        job_id = _worker_job_id()
        conn.execute(
            f"""
            INSERT INTO worker_jobs (
                worker_job_id, tenant_id, org_id, queue_name, job_type, status,
                priority, attempt_count, max_attempts, idempotency_key, correlation_id,
                payload, created_by, trace_id, created_at, updated_at, next_run_at
            ) VALUES (?, ?, ?, ?, ?, 'queued', ?, 0, ?, ?, ?, ?, ?, ?, {_now_expr()}, {_now_expr()}, COALESCE(?, {_now_expr()}))
            """,
            (job_id, ctx.tenant_id, ctx.org_id, queue_name, job_type, int(payload.get("priority") or 50), int(payload.get("maxAttempts") or payload.get("max_attempts") or 3), idempotency_key, payload.get("correlationId") or payload.get("correlation_id") or trace_id, dumps(job_payload), ctx.user_id, trace_id, payload.get("nextRunAt") or payload.get("next_run_at")),
        )
        row = conn.execute("SELECT * FROM worker_jobs WHERE worker_job_id = ?", (job_id,)).fetchone()
        conn.commit()
    job = _row_to_worker_job(row)
    write_audit_log(ctx, trace_id=trace_id, event_type="worker_job.queued", resource_type="worker_job", resource_id=job_id, action=job_type, status="queued", payload={"queueName": queue_name})
    return {"version": WORKER_QUEUE_VERSION, "created": True, "job": job}


def claim_next_worker_job(ctx: UserContext, *, queue_name: str = "default", worker_id: str = "worker-demo") -> Dict[str, Any] | None:
    ensure_worker_queue_tables()
    with connect() as conn:
        row = conn.execute(
            f"""
            SELECT * FROM worker_jobs
            WHERE tenant_id = ? AND queue_name = ? AND deleted_at IS NULL
              AND status IN ('queued', 'retry_scheduled')
              AND COALESCE(next_run_at, {_now_expr()}) <= {_now_expr()}
            ORDER BY priority ASC, created_at ASC
            LIMIT 1
            """,
            (ctx.tenant_id, queue_name),
        ).fetchone()
        if not row:
            return None
        conn.execute(
            f"""
            UPDATE worker_jobs
            SET status = 'claimed', claimed_by = ?, claimed_at = {_now_expr()},
                attempt_count = attempt_count + 1, updated_at = {_now_expr()}
            WHERE worker_job_id = ? AND tenant_id = ? AND status IN ('queued', 'retry_scheduled')
            """,
            (worker_id, row["worker_job_id"], ctx.tenant_id),
        )
        claimed = conn.execute("SELECT * FROM worker_jobs WHERE worker_job_id = ?", (row["worker_job_id"],)).fetchone()
        conn.commit()
    job = _row_to_worker_job(claimed)
    write_audit_log(ctx, trace_id=job.get("traceId") or resolve_trace_id(job.get("payload")), event_type="worker_job.claimed", resource_type="worker_job", resource_id=job["workerJobId"], action=job.get("jobType"), status="claimed", payload={"workerId": worker_id})
    return {"version": WORKER_QUEUE_VERSION, "job": job}


def complete_worker_job(ctx: UserContext, worker_job_id: str, result: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
    ensure_worker_queue_tables()
    with connect() as conn:
        conn.execute(f"""UPDATE worker_jobs SET status = 'completed', result = ?, error_message = NULL, finished_at = {_now_expr()}, updated_at = {_now_expr()} WHERE worker_job_id = ? AND tenant_id = ? AND deleted_at IS NULL""", (dumps(result or {}), worker_job_id, ctx.tenant_id))
        row = conn.execute("SELECT * FROM worker_jobs WHERE worker_job_id = ? AND tenant_id = ?", (worker_job_id, ctx.tenant_id)).fetchone()
        conn.commit()
    if not row:
        return None
    job = _row_to_worker_job(row)
    write_audit_log(ctx, trace_id=job.get("traceId") or resolve_trace_id(job.get("payload")), event_type="worker_job.completed", resource_type="worker_job", resource_id=worker_job_id, action=job.get("jobType"), status="completed", payload={"resultKeys": list((result or {}).keys())})
    return {"version": WORKER_QUEUE_VERSION, "job": job}


def fail_worker_job(ctx: UserContext, worker_job_id: str, *, error_message: str, retry: bool = True) -> Dict[str, Any] | None:
    ensure_worker_queue_tables()
    with connect() as conn:
        row = conn.execute("SELECT * FROM worker_jobs WHERE worker_job_id = ? AND tenant_id = ? AND deleted_at IS NULL", (worker_job_id, ctx.tenant_id)).fetchone()
        if not row:
            return None
        can_retry = retry and int(row["attempt_count"] or 0) < int(row["max_attempts"] or 3)
        next_status = "retry_scheduled" if can_retry else "failed"
        finished_expr = "NULL" if can_retry else _now_expr()
        conn.execute(f"""UPDATE worker_jobs SET status = ?, error_message = ?, next_run_at = CASE WHEN ? THEN datetime('now', '+1 minute') ELSE next_run_at END, finished_at = {finished_expr}, updated_at = {_now_expr()} WHERE worker_job_id = ? AND tenant_id = ?""", (next_status, error_message, 1 if can_retry else 0, worker_job_id, ctx.tenant_id))
        updated = conn.execute("SELECT * FROM worker_jobs WHERE worker_job_id = ?", (worker_job_id,)).fetchone()
        conn.commit()
    job = _row_to_worker_job(updated)
    write_audit_log(ctx, trace_id=job.get("traceId") or resolve_trace_id(job.get("payload")), event_type=f"worker_job.{next_status}", resource_type="worker_job", resource_id=worker_job_id, action=job.get("jobType"), status=next_status, payload={"error": error_message, "retry": can_retry})
    return {"version": WORKER_QUEUE_VERSION, "job": job}


def retry_worker_job(ctx: UserContext, worker_job_id: str) -> Dict[str, Any] | None:
    ensure_worker_queue_tables()
    with connect() as conn:
        conn.execute(f"""UPDATE worker_jobs SET status = 'queued', error_message = NULL, next_run_at = {_now_expr()}, updated_at = {_now_expr()} WHERE worker_job_id = ? AND tenant_id = ? AND deleted_at IS NULL AND status IN ('failed', 'retry_scheduled')""", (worker_job_id, ctx.tenant_id))
        row = conn.execute("SELECT * FROM worker_jobs WHERE worker_job_id = ? AND tenant_id = ?", (worker_job_id, ctx.tenant_id)).fetchone()
        conn.commit()
    if not row:
        return None
    job = _row_to_worker_job(row)
    write_audit_log(ctx, trace_id=job.get("traceId") or resolve_trace_id(job.get("payload")), event_type="worker_job.retry", resource_type="worker_job", resource_id=worker_job_id, action=job.get("jobType"), status="queued", payload={})
    return {"version": WORKER_QUEUE_VERSION, "job": job}


def list_worker_jobs(ctx: UserContext, *, queue_name: str | None = None, status: str | None = None, limit: int = 100) -> Dict[str, Any]:
    ensure_worker_queue_tables()
    where = ["tenant_id = ?", "deleted_at IS NULL"]
    params: list[Any] = [ctx.tenant_id]
    if queue_name:
        where.append("queue_name = ?")
        params.append(queue_name)
    if status:
        where.append("status = ?")
        params.append(status)
    params.append(limit)
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM worker_jobs WHERE {' AND '.join(where)} ORDER BY created_at DESC LIMIT ?", params).fetchall()
    return {"version": WORKER_QUEUE_VERSION, "count": len(rows), "jobs": [_row_to_worker_job(row) for row in rows]}


def worker_queue_summary(ctx: UserContext) -> Dict[str, Any]:
    ensure_worker_queue_tables()
    with connect() as conn:
        rows = conn.execute("""SELECT status, COUNT(*) AS total FROM worker_jobs WHERE tenant_id = ? AND deleted_at IS NULL GROUP BY status""", (ctx.tenant_id,)).fetchall()
    counts = {row["status"]: row["total"] for row in rows}
    return {"version": WORKER_QUEUE_VERSION, "mode": "sqlite_worker_queue_scaffold", "tenantId": ctx.tenant_id, "counts": counts, "activeTotal": sum(counts.get(status, 0) for status in ACTIVE_STATUSES), "terminalTotal": sum(counts.get(status, 0) for status in TERMINAL_STATUSES), "supportedJobTypes": sorted(SUPPORTED_JOB_TYPES), "nextStep": "Worker queue now carries trace_id and audit_logs."}
