"""Repository runtime transition service."""

from __future__ import annotations

import os
from typing import Any, Dict

from sqlalchemy import text

from src.core.context import UserContext
from src.db.repositories import production_repository_summary
from src.db.session import database_runtime_summary, get_session_factory

REPOSITORY_RUNTIME_VERSION = "5.3.2"
SUPPORTED_MODES = {"sqlite", "postgres", "hybrid"}


def repository_mode() -> str:
    mode = os.getenv("DB_REPOSITORY_MODE", "sqlite").lower()
    return mode if mode in SUPPORTED_MODES else "sqlite"


def _task_mirror_summary(mode: str) -> Dict[str, Any]:
    return {
        "version": REPOSITORY_RUNTIME_VERSION,
        "mode": mode,
        "enabled": mode in {"hybrid", "postgres"},
        "sqliteFirst": True,
        "rule": "Task writes succeed in SQLite first; PostgreSQL mirror failure never breaks Demo runtime in hybrid mode.",
    }


def repository_runtime_summary(ctx: UserContext) -> Dict[str, Any]:
    mode = repository_mode()
    return {
        "version": REPOSITORY_RUNTIME_VERSION,
        "activeMode": mode,
        "sqliteDemoFallback": mode in {"sqlite", "hybrid"},
        "postgresRepositoryEnabled": mode in {"postgres", "hybrid"},
        "taskHybridMirror": _task_mirror_summary(mode),
        "currentContext": ctx.to_dict(),
        "database": database_runtime_summary(),
        "productionRepositories": production_repository_summary(),
        "switchEnv": {"DB_REPOSITORY_MODE": "sqlite | hybrid | postgres", "current": mode, "safeDefault": "sqlite"},
        "rule": "Task writes are SQLite-first and optionally mirrored to PostgreSQL in hybrid/postgres mode.",
    }


async def repository_health_check(ctx: UserContext) -> Dict[str, Any]:
    mode = repository_mode()
    result: Dict[str, Any] = repository_runtime_summary(ctx)
    if mode == "sqlite":
        result["postgresHealth"] = {"checked": False, "reason": "DB_REPOSITORY_MODE=sqlite keeps Demo runtime active."}
        return result
    try:
        async with get_session_factory()() as session:
            value = (await session.execute(text("SELECT 1 AS ok"))).mappings().first()
        result["postgresHealth"] = {"checked": True, "ok": bool(value and value.get("ok") == 1), "error": None}
    except Exception as exc:  # noqa: BLE001
        result["postgresHealth"] = {"checked": True, "ok": False, "error": str(exc), "fallback": mode == "hybrid"}
    return result
