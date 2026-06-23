"""JSON TechLog service with sensitive data redaction."""

from __future__ import annotations

from typing import Any, Dict
from uuid import uuid4

from src.core.context import UserContext
from src.repositories.sqlite_repository import connect, dumps, init_db, loads

TECH_LOG_VERSION = "5.2.7"
REDACTED = "[REDACTED]"
SENSITIVE_KEYWORDS = (
    "token",
    "password",
    "passwd",
    "secret",
    "api_key",
    "apikey",
    "access_key",
    "private_key",
    "authorization",
    "cookie",
    "set-cookie",
    "session",
    "credential",
    "bearer",
)


def _log_id() -> str:
    return f"TECHLOG_{uuid4().hex[:12]}".upper()


def _is_sensitive_key(key: Any) -> bool:
    lowered = str(key).lower().replace("-", "_")
    return any(word in lowered for word in SENSITIVE_KEYWORDS)


def redact_sensitive_payload(value: Any, *, max_depth: int = 8) -> Any:
    """Recursively redact secrets from dict/list payloads before persistence."""

    if max_depth <= 0:
        return "[MAX_DEPTH]"
    if isinstance(value, dict):
        result: Dict[str, Any] = {}
        for key, item in value.items():
            if _is_sensitive_key(key):
                result[str(key)] = REDACTED
            else:
                result[str(key)] = redact_sensitive_payload(item, max_depth=max_depth - 1)
        return result
    if isinstance(value, list):
        return [redact_sensitive_payload(item, max_depth=max_depth - 1) for item in value]
    if isinstance(value, tuple):
        return [redact_sensitive_payload(item, max_depth=max_depth - 1) for item in value]
    if isinstance(value, str):
        lowered = value.lower()
        if lowered.startswith("bearer ") or lowered.startswith("basic "):
            return REDACTED
        if "password=" in lowered or "token=" in lowered or "api_key=" in lowered:
            return REDACTED
    return value


def ensure_tech_log_tables() -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tech_logs (
                log_id TEXT PRIMARY KEY,
                trace_id TEXT,
                tenant_id TEXT DEFAULT 'tenant_demo',
                org_id TEXT DEFAULT 'org_demo',
                actor_id TEXT,
                level TEXT NOT NULL,
                logger TEXT,
                event_type TEXT NOT NULL,
                message TEXT,
                payload TEXT,
                created_at TEXT NOT NULL,
                deleted_at TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tech_logs_trace ON tech_logs(trace_id, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tech_logs_tenant_event ON tech_logs(tenant_id, event_type, created_at)")
        conn.commit()


def write_tech_log(
    ctx: UserContext,
    *,
    level: str = "info",
    event_type: str,
    message: str | None = None,
    payload: Dict[str, Any] | None = None,
    trace_id: str | None = None,
    logger: str = "app",
) -> Dict[str, Any]:
    """Persist a sanitized technical log entry."""

    ensure_tech_log_tables()
    log_id = _log_id()
    safe_payload = redact_sensitive_payload(payload or {})
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO tech_logs (
                log_id, trace_id, tenant_id, org_id, actor_id, level, logger,
                event_type, message, payload, created_at, deleted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), NULL)
            """,
            (log_id, trace_id, ctx.tenant_id, ctx.org_id, ctx.user_id, level.lower(), logger, event_type, message, dumps(safe_payload)),
        )
        conn.commit()
    return {"version": TECH_LOG_VERSION, "logId": log_id, "traceId": trace_id, "eventType": event_type, "level": level.lower(), "redacted": True}


def list_tech_logs(ctx: UserContext, *, trace_id: str | None = None, level: str | None = None, event_type: str | None = None, limit: int = 100) -> Dict[str, Any]:
    ensure_tech_log_tables()
    where = ["tenant_id = ?", "deleted_at IS NULL"]
    params: list[Any] = [ctx.tenant_id]
    if trace_id:
        where.append("trace_id = ?")
        params.append(trace_id)
    if level:
        where.append("level = ?")
        params.append(level.lower())
    if event_type:
        where.append("event_type = ?")
        params.append(event_type)
    params.append(limit)
    with connect() as conn:
        rows = conn.execute(
            f"SELECT * FROM tech_logs WHERE {' AND '.join(where)} ORDER BY created_at DESC LIMIT ?",
            params,
        ).fetchall()
    logs = []
    for row in rows:
        logs.append({
            "logId": row["log_id"],
            "traceId": row["trace_id"],
            "tenantId": row["tenant_id"],
            "orgId": row["org_id"],
            "actorId": row["actor_id"],
            "level": row["level"],
            "logger": row["logger"],
            "eventType": row["event_type"],
            "message": row["message"],
            "payload": loads(row["payload"]),
            "createdAt": row["created_at"],
        })
    return {"version": TECH_LOG_VERSION, "count": len(logs), "logs": logs}


def tech_log_summary() -> Dict[str, Any]:
    ensure_tech_log_tables()
    with connect() as conn:
        rows = conn.execute("SELECT level, COUNT(*) AS total FROM tech_logs WHERE deleted_at IS NULL GROUP BY level").fetchall()
    return {
        "version": TECH_LOG_VERSION,
        "redaction": "enabled",
        "redactedKeywords": list(SENSITIVE_KEYWORDS),
        "counts": {row["level"]: row["total"] for row in rows},
        "rule": "Business audit is stored in audit_logs; technical JSON logs are stored in tech_logs after redaction.",
    }
