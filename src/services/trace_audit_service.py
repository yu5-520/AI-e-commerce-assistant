"""Trace and audit log service for P0 runtime."""

from __future__ import annotations

from typing import Any, Dict
from uuid import uuid4

from src.core.context import UserContext
from src.repositories.sqlite_repository import connect, dumps, init_db, loads
from src.services.audit_tech_repository_mirror_service import mirror_audit_log_to_production
from src.services.tech_log_service import redact_sensitive_payload, write_tech_log

TRACE_AUDIT_VERSION = "5.3.4"


def make_trace_id(prefix: str = "TRACE") -> str:
    return f"{prefix}_{uuid4().hex[:12]}".upper()


def make_audit_id() -> str:
    return f"AUDIT_{uuid4().hex[:12]}".upper()


def resolve_trace_id(payload: Dict[str, Any] | None = None, fallback_prefix: str = "TRACE") -> str:
    payload = payload or {}
    return str(payload.get("traceId") or payload.get("trace_id") or payload.get("correlationId") or payload.get("correlation_id") or make_trace_id(fallback_prefix))


def ensure_trace_audit_tables() -> None:
    init_db()
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                audit_id TEXT PRIMARY KEY, trace_id TEXT NOT NULL, tenant_id TEXT DEFAULT 'tenant_demo', org_id TEXT DEFAULT 'org_demo',
                actor_id TEXT, event_type TEXT NOT NULL, resource_type TEXT, resource_id TEXT, action TEXT,
                status TEXT, payload TEXT, created_at TEXT NOT NULL, deleted_at TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_trace ON audit_logs(trace_id, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant_event ON audit_logs(tenant_id, event_type, created_at)")
        for table in ["import_jobs", "projection_jobs", "worker_jobs", "worker_task_results"]:
            try:
                columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
                if columns and "trace_id" not in columns:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN trace_id TEXT")
            except Exception:
                pass
        conn.commit()


def write_audit_log(ctx: UserContext, *, trace_id: str, event_type: str, resource_type: str | None = None, resource_id: str | None = None, action: str | None = None, status: str | None = None, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    ensure_trace_audit_tables()
    audit_id = make_audit_id()
    safe_payload = redact_sensitive_payload(payload or {})
    with connect() as conn:
        conn.execute("""
            INSERT INTO audit_logs (
                audit_id, trace_id, tenant_id, org_id, actor_id, event_type,
                resource_type, resource_id, action, status, payload, created_at, deleted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), NULL)
        """, (audit_id, trace_id, ctx.tenant_id, ctx.org_id, ctx.user_id, event_type, resource_type, resource_id, action, status, dumps(safe_payload)))
        conn.commit()
    audit_payload = {"auditId": audit_id, "traceId": trace_id, "tenantId": ctx.tenant_id, "orgId": ctx.org_id, "actorId": ctx.user_id, "eventType": event_type, "resourceType": resource_type, "resourceId": resource_id, "action": action, "status": status, "payload": safe_payload}
    production_mirror = mirror_audit_log_to_production(ctx, audit_payload, action="audit_log.write")
    tech = write_tech_log(ctx, trace_id=trace_id, level="info", logger="audit", event_type=f"audit.{event_type}", message="business audit event persisted", payload={"auditId": audit_id, "resourceType": resource_type, "resourceId": resource_id, "action": action, "status": status, "payload": safe_payload})
    return {"version": TRACE_AUDIT_VERSION, "auditId": audit_id, "traceId": trace_id, "eventType": event_type, "status": status, "productionMirror": production_mirror, "techLog": tech}


def set_resource_trace(table: str, id_column: str, resource_id: str, trace_id: str, tenant_id: str | None = None) -> None:
    ensure_trace_audit_tables()
    allowed = {"import_jobs": "import_job_id", "projection_jobs": "projection_job_id", "worker_jobs": "worker_job_id", "worker_task_results": "result_id"}
    if allowed.get(table) != id_column:
        return
    with connect() as conn:
        if tenant_id:
            conn.execute(f"UPDATE {table} SET trace_id = ? WHERE {id_column} = ? AND tenant_id = ?", (trace_id, resource_id, tenant_id))
        else:
            conn.execute(f"UPDATE {table} SET trace_id = ? WHERE {id_column} = ?", (trace_id, resource_id))
        conn.commit()


def audit_timeline(ctx: UserContext, trace_id: str, limit: int = 100) -> Dict[str, Any]:
    ensure_trace_audit_tables()
    with connect() as conn:
        rows = conn.execute("""
            SELECT * FROM audit_logs
            WHERE tenant_id = ? AND trace_id = ? AND deleted_at IS NULL
            ORDER BY created_at ASC
            LIMIT ?
        """, (ctx.tenant_id, trace_id, limit)).fetchall()
    events = [{"auditId": row["audit_id"], "traceId": row["trace_id"], "eventType": row["event_type"], "resourceType": row["resource_type"], "resourceId": row["resource_id"], "action": row["action"], "status": row["status"], "payload": loads(row["payload"]), "actorId": row["actor_id"], "createdAt": row["created_at"]} for row in rows]
    return {"version": TRACE_AUDIT_VERSION, "traceId": trace_id, "count": len(events), "events": events}
