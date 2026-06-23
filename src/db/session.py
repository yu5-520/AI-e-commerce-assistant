"""Async SQLAlchemy session configuration for production PostgreSQL.

This module is intentionally not wired into the current SQLite Demo services yet.
It provides the V5.3.0 production database boundary for future migration.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

DATABASE_LAYER_VERSION = "5.3.0"
DEFAULT_DATABASE_URL = "postgresql+asyncpg://user:password@127.0.0.1:5432/ai_ecommerce"


@dataclass(frozen=True)
class DatabaseSettings:
    url: str
    pool_size: int
    max_overflow: int
    pool_timeout: int
    echo: bool
    demo_sqlite_url: str


def database_settings() -> DatabaseSettings:
    return DatabaseSettings(
        url=os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
        pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
        pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
        echo=os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true",
        demo_sqlite_url=os.getenv("DEMO_DATABASE_URL", "sqlite+aiosqlite:///./runtime/ai_ecommerce_demo.db"),
    )


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_async_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = database_settings()
        _engine = create_async_engine(
            settings.url,
            echo=settings.echo,
            pool_size=settings.pool_size,
            max_overflow=settings.max_overflow,
            pool_timeout=settings.pool_timeout,
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(get_async_engine(), expire_on_commit=False)
    return _session_factory


async def get_async_session() -> AsyncIterator[AsyncSession]:
    async with get_session_factory()() as session:
        yield session


def database_runtime_summary() -> dict[str, object]:
    settings = database_settings()
    return {
        "version": DATABASE_LAYER_VERSION,
        "databaseUrlConfigured": bool(settings.url),
        "databaseDriver": settings.url.split(":", 1)[0] if settings.url else None,
        "poolSize": settings.pool_size,
        "maxOverflow": settings.max_overflow,
        "poolTimeout": settings.pool_timeout,
        "echo": settings.echo,
        "demoSqliteUrl": settings.demo_sqlite_url,
        "rule": "SQLite services remain active for Demo; PostgreSQL async session is the production migration target.",
    }
