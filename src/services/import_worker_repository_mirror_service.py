"""ImportJob and WorkerJob PostgreSQL mirror service.

SQLite Demo remains the source of truth in V5.3.3. This service mirrors successful
ImportJob and WorkerJob writes into production SQLAlchemy repositories when
DB_REPOSITORY_MODE is hybrid or postgres.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from src.core.context import UserContext
from src.db.repositories import ProductionImportJobRepository, ProductionWorkerJobRepository
from src.db.session import get_session_factory
from src.services.repository_runtime_service import repository_mode
from src.services.trace_audit_service import write_audit_log

IMPORT_WORKER_MIRROR_VERSION = "5.3.3"


def _skipped(action: str, reason: str = "DB_REPOSITORY_MODE=sqlite") -> Dict[str, Any]:
    return {"version": IMPORT_WORKER_MIRROR_VERSION, "action": action, "mode": repository_mode(), "mirrored": False, "status": "skipped", "reason": reason}


def _run(coro: Any, action: str) -> Dict[str, Any]:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    return {"version": IMPORT_WORKER_MIRROR_VERSION, "action": action, "mirrored": False, "status": "skipped", "reason": "event_loop_running; use async mirror path later"}


async def _mirror_import_async(ctx: UserContext, job: Dict[str, Any], action: str) -> Dict[str, Any]:
    async with get_session_factory()() as session:
        repo = ProductionImportJobRepository(session, ctx)
        mirrored = await repo.upsert(job)
        await session.commit()
    write_audit_log(ctx, trace_id=mirrored.get("traceId") or job.get("traceId") or "IMPORT_MIRROR", event_type="import_job.production_mirrored", resource_type="import_job", resource_id=mirrored.get("importJobId"), action=action, status="mirrored", payload={"mode": repository_mode(), "status": mirrored.get("status")})
    return {"version": IMPORT_WORKER_MIRROR_VERSION, "action": action, "mode": repository_mode(), "mirrored": True, "status": "mirrored", "importJob": mirrored}


async def _mirror_worker_async(ctx: UserContext, job: Dict[str, Any], action: str) -> Dict[str, Any]:
    async with get_session_factory()() as session:
        repo = ProductionWorkerJobRepository(session, ctx)
        mirrored = await repo.upsert(job)
        await session.commit()
    write_audit_log(ctx, trace_id=mirrored.get("traceId") or job.get("traceId") or "WORKER_MIRROR", event_type="worker_job.production_mirrored", resource_type="worker_job", resource_id=mirrored.get("workerJobId"), action=action, status="mirrored", payload={"mode": repository_mode(), "status": mirrored.get("status")})
    return {"version": IMPORT_WORKER_MIRROR_VERSION, "action": action, "mode": repository_mode(), "mirrored": True, "status": "mirrored", "workerJob": mirrored}


def mirror_import_job_to_production(ctx: UserContext, job: Dict[str, Any] | None, *, action: str) -> Dict[str, Any]:
    mode = repository_mode()
    if mode == "sqlite":
        return _skipped(action)
    if not job:
        return _skipped(action, "import job is empty")
    try:
        return _run(_mirror_import_async(ctx, job, action), action)
    except Exception as exc:  # noqa: BLE001
        return {"version": IMPORT_WORKER_MIRROR_VERSION, "action": action, "mode": mode, "mirrored": False, "status": "failed", "error": str(exc), "fallback": mode == "hybrid"}


def mirror_worker_job_to_production(ctx: UserContext, job: Dict[str, Any] | None, *, action: str) -> Dict[str, Any]:
    mode = repository_mode()
    if mode == "sqlite":
        return _skipped(action)
    if not job:
        return _skipped(action, "worker job is empty")
    try:
        return _run(_mirror_worker_async(ctx, job, action), action)
    except Exception as exc:  # noqa: BLE001
        return {"version": IMPORT_WORKER_MIRROR_VERSION, "action": action, "mode": mode, "mirrored": False, "status": "failed", "error": str(exc), "fallback": mode == "hybrid"}


def import_worker_mirror_summary() -> Dict[str, Any]:
    mode = repository_mode()
    return {"version": IMPORT_WORKER_MIRROR_VERSION, "mode": mode, "enabled": mode in {"hybrid", "postgres"}, "sqliteFirst": True, "mirroredResources": ["ImportJob", "WorkerJob"], "rule": "ImportJob and WorkerJob writes succeed in SQLite first; PostgreSQL mirror failure never breaks Demo runtime in hybrid mode."}
