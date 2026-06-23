"""TaskRepository PostgreSQL mirror service.

SQLite Demo remains the source of truth in V5.3.2. This service mirrors
successful task writes into the production SQLAlchemy repository when
DB_REPOSITORY_MODE is hybrid or postgres.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from src.core.context import UserContext
from src.db.repositories import ProductionTaskRepository, production_repository_summary
from src.db.session import get_session_factory
from src.services.repository_runtime_service import repository_mode
from src.services.trace_audit_service import write_audit_log

TASK_REPOSITORY_MIRROR_VERSION = "5.3.2"


def _skipped(action: str, reason: str = "DB_REPOSITORY_MODE=sqlite") -> Dict[str, Any]:
    return {"version": TASK_REPOSITORY_MIRROR_VERSION, "action": action, "mode": repository_mode(), "mirrored": False, "status": "skipped", "reason": reason}


def _run(coro: Any, action: str) -> Dict[str, Any]:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    return {"version": TASK_REPOSITORY_MIRROR_VERSION, "action": action, "mirrored": False, "status": "skipped", "reason": "event_loop_running; use async mirror path later"}


async def _mirror_task_async(ctx: UserContext, task: Dict[str, Any], action: str) -> Dict[str, Any]:
    async with get_session_factory()() as session:
        repo = ProductionTaskRepository(session, ctx)
        mirrored = await repo.upsert(task)
        await session.commit()
    write_audit_log(ctx, trace_id=task.get("traceId") or task.get("trace_id") or "TASK_MIRROR", event_type="task.production_mirrored", resource_type="decision_task", resource_id=mirrored.get("taskId"), action=action, status="mirrored", payload={"mode": repository_mode()})
    return {"version": TASK_REPOSITORY_MIRROR_VERSION, "action": action, "mode": repository_mode(), "mirrored": True, "status": "mirrored", "task": mirrored}


async def _soft_delete_async(ctx: UserContext, reason: str, trace_id: str) -> Dict[str, Any]:
    async with get_session_factory()() as session:
        repo = ProductionTaskRepository(session, ctx)
        deleted = await repo.soft_delete_visible(reason=reason)
        await session.commit()
    write_audit_log(ctx, trace_id=trace_id, event_type="task.production_soft_deleted", resource_type="decision_task", resource_id="visible_tasks", action="reset_tasks", status="mirrored", payload={"softDeletedTasks": deleted, "mode": repository_mode()})
    return {"version": TASK_REPOSITORY_MIRROR_VERSION, "action": "reset_tasks", "mode": repository_mode(), "mirrored": True, "status": "mirrored", "softDeletedTasks": deleted}


def mirror_task_to_production(ctx: UserContext, task: Dict[str, Any] | None, *, action: str) -> Dict[str, Any]:
    mode = repository_mode()
    if mode == "sqlite":
        return _skipped(action)
    if not task:
        return _skipped(action, "task is empty")
    try:
        return _run(_mirror_task_async(ctx, task, action), action)
    except Exception as exc:  # noqa: BLE001
        return {"version": TASK_REPOSITORY_MIRROR_VERSION, "action": action, "mode": mode, "mirrored": False, "status": "failed", "error": str(exc), "fallback": mode == "hybrid"}


def mirror_task_reset_to_production(ctx: UserContext, *, reason: str, trace_id: str) -> Dict[str, Any]:
    mode = repository_mode()
    if mode == "sqlite":
        return _skipped("reset_tasks")
    try:
        return _run(_soft_delete_async(ctx, reason, trace_id), "reset_tasks")
    except Exception as exc:  # noqa: BLE001
        return {"version": TASK_REPOSITORY_MIRROR_VERSION, "action": "reset_tasks", "mode": mode, "mirrored": False, "status": "failed", "error": str(exc), "fallback": mode == "hybrid"}


def task_repository_mirror_summary() -> Dict[str, Any]:
    return {"version": TASK_REPOSITORY_MIRROR_VERSION, "mode": repository_mode(), "enabled": repository_mode() in {"hybrid", "postgres"}, "sqliteFirst": True, "productionRepository": production_repository_summary(), "rule": "Task writes succeed in SQLite first; PostgreSQL mirror failure never breaks Demo runtime in hybrid mode."}
