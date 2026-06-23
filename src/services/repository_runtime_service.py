"""Repository runtime transition service.

V5.3.1 keeps SQLite as the default Demo runtime while exposing PostgreSQL
repository readiness and switch controls through DB_REPOSITORY_MODE.
"""

from __future__ import annotations

import os
from typing import Any, Dict

from sqlalchemy import text

from src.core.context import UserContext
from src.db.repositories import production_repository_summary
from src.db.session import database_runtime_summary, get_session_factory

REPOSITORY_RUNTIME_VERSION = "5.3.1"
SUPPORTED_MODES = {"sqlite", "postgres", "hybrid"}


def repository_mode() -> str:
    mode = os.getenv("DB_REPOSITORY_MODE", "sqlite").lower()
    return mode if mode in SUPPORTED_MODES else "sqlite"


def repository_runtime_summary(ctx: UserContext) -> Dict[str, Any]:
    mode = repository_mode()
    return {
        "version": REPOSITORY_RUNTIME_VERSION,
        "activeMode": mode,
        "sqliteDemoFallback": mode in {"sqlite", "hybrid"},
        "postgresRepositoryEnabled": mode in {"postgres", "hybrid"},
        "currentContext": ctx.to_dict(),
        "database": database_runtime_summary(),
        "productionRepositories": production_repository_summary(),
        "switchEnv": {
            "DB_REPOSITORY_MODE": "sqlite | hybrid | postgres",
            "current": mode,
            "safeDefault": "sqlite",
        },
        "rule": "Routes remain on SQLite Demo unless explicitly migrated; production repositories can be tested through health checks first.",
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
