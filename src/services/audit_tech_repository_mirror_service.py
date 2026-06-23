"""AuditLog and TechLog PostgreSQL mirror service.

This service mirrors already-persisted SQLite audit/tech log entries into PostgreSQL.
It intentionally does not write additional audit records to avoid recursive audit logging.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from src.core.context import UserContext
from src.db.repositories import ProductionAuditRepository, ProductionTechLogRepository
from src.db.session import get_session_factory
from src.services.repository_runtime_service import repository_mode

AUDIT_TECH_MIRROR_VERSION = "5.3.4"


def _skipped(action: str, reason: str = "DB_REPOSITORY_MODE=sqlite") -> Dict[str, Any]:
    return {"version": AUDIT_TECH_MIRROR_VERSION, "action": action, "mode": repository_mode(), "mirrored": False, "status": "skipped", "reason": reason}


def _run(coro: Any, action: str) -> Dict[str, Any]:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    return {"version": AUDIT_TECH_MIRROR_VERSION, "action": action, "mirrored": False, "status": "skipped", "reason": "event_loop_running; use async mirror path later"}


async def _mirror_audit_async(ctx: UserContext, payload: Dict[str, Any], action: str) -> Dict[str, Any]:
    async with get_session_factory()() as session:
        repo = ProductionAuditRepository(session, ctx)
        mirrored = await repo.upsert(payload)
        await session.commit()
    return {"version": AUDIT_TECH_MIRROR_VERSION, "action": action, "mode": repository_mode(), "mirrored": True, "status": "mirrored", "auditLog": mirrored}


async def _mirror_tech_async(ctx: UserContext, payload: Dict[str, Any], action: str) -> Dict[str, Any]:
    async with get_session_factory()() as session:
        repo = ProductionTechLogRepository(session, ctx)
        mirrored = await repo.upsert(payload)
        await session.commit()
    return {"version": AUDIT_TECH_MIRROR_VERSION, "action": action, "mode": repository_mode(), "mirrored": True, "status": "mirrored", "techLog": mirrored}


def mirror_audit_log_to_production(ctx: UserContext, payload: Dict[str, Any] | None, *, action: str = "audit_log.write") -> Dict[str, Any]:
    mode = repository_mode()
    if mode == "sqlite":
        return _skipped(action)
    if not payload:
        return _skipped(action, "audit payload is empty")
    try:
        return _run(_mirror_audit_async(ctx, payload, action), action)
    except Exception as exc:  # noqa: BLE001
        return {"version": AUDIT_TECH_MIRROR_VERSION, "action": action, "mode": mode, "mirrored": False, "status": "failed", "error": str(exc), "fallback": mode == "hybrid"}


def mirror_tech_log_to_production(ctx: UserContext, payload: Dict[str, Any] | None, *, action: str = "tech_log.write") -> Dict[str, Any]:
    mode = repository_mode()
    if mode == "sqlite":
        return _skipped(action)
    if not payload:
        return _skipped(action, "tech payload is empty")
    try:
        return _run(_mirror_tech_async(ctx, payload, action), action)
    except Exception as exc:  # noqa: BLE001
        return {"version": AUDIT_TECH_MIRROR_VERSION, "action": action, "mode": mode, "mirrored": False, "status": "failed", "error": str(exc), "fallback": mode == "hybrid"}


def audit_tech_mirror_summary() -> Dict[str, Any]:
    mode = repository_mode()
    return {"version": AUDIT_TECH_MIRROR_VERSION, "mode": mode, "enabled": mode in {"hybrid", "postgres"}, "sqliteFirst": True, "mirroredResources": ["AuditLog", "TechLog"], "rule": "AuditLog and TechLog write to SQLite first; PostgreSQL mirror failure never breaks Demo runtime in hybrid mode."}
