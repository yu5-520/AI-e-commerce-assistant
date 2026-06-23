"""Declarative base and production ORM mixins."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

ORM_BASE_VERSION = "5.3.0"


class Base(DeclarativeBase):
    """Production SQLAlchemy declarative base."""

    type_annotation_map = {dict[str, Any]: String}


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class TenantScopedMixin:
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    org_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    @declared_attr.directive
    def __table_args__(cls) -> tuple[Any, ...]:
        return (Index(f"idx_{cls.__tablename__}_tenant_org", "tenant_id", "org_id"),)


class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    deleted_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    delete_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)


class TraceAuditMixin:
    trace_id: Mapped[str | None] = mapped_column(String(96), nullable=True, index=True)


class ActorMixin:
    created_by: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    updated_by: Mapped[str | None] = mapped_column(String(64), nullable=True)


def orm_base_summary() -> dict[str, object]:
    return {
        "version": ORM_BASE_VERSION,
        "base": "src.db.base.Base",
        "mixins": ["TimestampMixin", "TenantScopedMixin", "SoftDeleteMixin", "TraceAuditMixin", "ActorMixin"],
        "rule": "Production tables should inherit tenant, soft delete, timestamp, and trace mixins instead of hand-writing these fields.",
    }
