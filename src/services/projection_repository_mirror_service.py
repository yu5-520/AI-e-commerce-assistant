"""ProjectionJob PostgreSQL mirror service.

SQLite Demo remains the source of truth in V5.3.5. ProjectionJob writes are mirrored
into PostgreSQL only when DB_REPOSITORY_MODE is hybrid or postgres.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from src.core.context import UserContext
from src.db.projection_repositories import ProductionProjectionJobRepository, projection_repository_summary
from src.db.session import get_session_factory
from src.services.repository_runtime_service import repository_mode

PROJECTION_MIRROR_VERSION = "5.3.5"


def _skipped(action: str, reason: str = "DB_REPOSITORY_MODE=sqlite") -> Dict[str, Any]:
    return {"version": PROJECTION_MIRROR_VERSION, "action": action, "mode": repository_mode(), "mirrored": False, "status": "skipped", "reason": reason}


def _run(coro: Any, action: str) -> Dict[str, Any]:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    return {"version": PROJECTION_MIRROR_VERSION, "action": action, "mirrored": False, "status": "skipped", "reason": "event_loop_running; use async mirror path later"}


async def _mirror_projection_async(ctx: UserContext, payload: Dict[str, Any], action: str) -> Dict[str, Any]:
    async with get_session_factory()() as session:
        repo = ProductionProjectionJobRepository(session, ctx)
        mirrored = await repo.upsert(payload)
        await session.commit()
    return {"version": PROJECTION_MIRROR_VERSION, "action": action, "mode": repository_mode(), "mirrored": True, "status": "mirrored", "projectionJob": mirrored}


def mirror_projection_job_to_production(ctx: UserContext, payload: Dict[str, Any] | None, *, action: str = "projection_job.write") -> Dict[str, Any]:
    mode = repository_mode()
    if mode == "sqlite":
        return _skipped(action)
    if not payload:
        return _skipped(action, "projection payload is empty")
    try:
        return _run(_mirror_projection_async(ctx, payload, action), action)
    except Exception as exc:  # noqa: BLE001
        return {"version": PROJECTION_MIRROR_VERSION, "action": action, "mode": mode, "mirrored": False, "status": "failed", "error": str(exc), "fallback": mode == "hybrid"}


def projection_mirror_summary() -> Dict[str, Any]:
    mode = repository_mode()
    return {"version": PROJECTION_MIRROR_VERSION, "mode": mode, "enabled": mode in {"hybrid", "postgres"}, "sqliteFirst": True, "mirroredResources": ["ProjectionJob"], "productionRepository": projection_repository_summary(), "rule": "ProjectionJob writes succeed in SQLite first; PostgreSQL mirror failure never breaks Demo runtime in hybrid mode."}
