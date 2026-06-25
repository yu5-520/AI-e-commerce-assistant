"""P0 scoped repository primitives.

The current product still uses a lightweight SQLite/demo storage layer in many
places. This module defines the shared SaaS scope contract first, so future
SQLAlchemy repositories can inherit the same tenant / soft-delete filtering rule
instead of re-implementing it in every route or service.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from src.core.context import UserContext


@dataclass(frozen=True)
class ScopeFilter:
    tenant_id: str
    org_id: str
    store_group_ids: list[str] = field(default_factory=list)
    store_ids: list[str] = field(default_factory=list)
    role_id: str = "observer"
    include_deleted: bool = False
    strict_scope: bool = False

    @classmethod
    def from_context(cls, ctx: UserContext, *, include_deleted: bool = False) -> "ScopeFilter":
        return cls(
            tenant_id=ctx.tenant_id,
            org_id=ctx.org_id,
            store_group_ids=list(ctx.store_group_ids),
            store_ids=list(ctx.store_ids),
            role_id=ctx.role_id,
            include_deleted=include_deleted,
            strict_scope=ctx.strict_scope,
        )


@dataclass(frozen=True)
class ScopedQueryPlan:
    """Human-readable query contract for architecture checks and future SQL builds."""

    where: list[str]
    params: dict[str, Any]
    rule: str = "tenant + org + soft delete + role data scope"


def query_plan_for_context(ctx: UserContext, *, table_alias: str = "resource", include_deleted: bool = False) -> ScopedQueryPlan:
    """Return the mandatory WHERE contract every repository must apply."""

    prefix = f"{table_alias}." if table_alias else ""
    where = [f"{prefix}tenant_id = :tenant_id", f"{prefix}org_id = :org_id"]
    params: dict[str, Any] = {"tenant_id": ctx.tenant_id, "org_id": ctx.org_id}
    if not include_deleted:
        where.append(f"{prefix}deleted_at IS NULL")
    if ctx.role_id == "owner":
        return ScopedQueryPlan(where=where, params=params)
    if ctx.role_id == "manager":
        where.append(f"{prefix}store_group_id IN :store_group_ids")
        params["store_group_ids"] = tuple(ctx.store_group_ids or ["__none__"])
        return ScopedQueryPlan(where=where, params=params)
    if ctx.role_id in {"operator", "finance", "observer"}:
        where.append(f"{prefix}store_id IN :store_ids")
        params["store_ids"] = tuple(ctx.store_ids or ["__none__"])
        return ScopedQueryPlan(where=where, params=params)
    where.append("1 = 0")
    return ScopedQueryPlan(where=where, params=params, rule="deny unknown role")


def _pick(item: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in item and item.get(name) not in {None, ""}:
            return item.get(name)
    return None


def item_visible_to_context(
    item: dict[str, Any],
    ctx: UserContext,
    *,
    include_deleted: bool = False,
    tenant_fields: tuple[str, ...] = ("tenantId", "tenant_id"),
    org_fields: tuple[str, ...] = ("orgId", "org_id"),
    store_fields: tuple[str, ...] = ("storeId", "store_id"),
    store_group_fields: tuple[str, ...] = ("storeGroupId", "store_group_id", "groupId", "group_id"),
    deleted_fields: tuple[str, ...] = ("deletedAt", "deleted_at"),
) -> bool:
    """Apply the same scope rule to dict-based demo rows.

    This is a bridge for existing services while database-backed repositories are
    introduced. Production repositories should enforce the same rule in SQL.
    """

    tenant_id = _pick(item, *tenant_fields)
    org_id = _pick(item, *org_fields)
    if ctx.strict_scope and not tenant_id:
        return False
    if tenant_id and tenant_id != ctx.tenant_id:
        return False
    if ctx.strict_scope and not org_id:
        return False
    if org_id and org_id != ctx.org_id:
        return False
    if not include_deleted and _pick(item, *deleted_fields):
        return False
    if ctx.role_id == "owner":
        return True
    store_group_id = _pick(item, *store_group_fields)
    store_id = _pick(item, *store_fields)
    if ctx.strict_scope and not store_group_id and not store_id:
        return False
    if ctx.role_id == "manager":
        if store_group_id:
            return store_group_id in set(ctx.store_group_ids)
        return (not ctx.strict_scope and not store_id) or store_id in set(ctx.store_ids)
    return (not ctx.strict_scope and not store_id) or store_id in set(ctx.store_ids)


def filter_visible_items(items: Iterable[dict[str, Any]], ctx: UserContext, *, include_deleted: bool = False) -> list[dict[str, Any]]:
    return [item for item in items if item_visible_to_context(item, ctx, include_deleted=include_deleted)]


class ScopedRepositoryBase:
    """Base class contract for future SQLAlchemy repositories.

    P0 rule: route handlers must call repository/service methods with UserContext;
    repositories apply tenant, org, deleted_at and role data-scope filters centrally.
    """

    resource_name = "resource"

    def __init__(self, ctx: UserContext) -> None:
        self.ctx = ctx
        self.scope = ScopeFilter.from_context(ctx)

    def query_plan(self, *, table_alias: str | None = None, include_deleted: bool = False) -> ScopedQueryPlan:
        return query_plan_for_context(self.ctx, table_alias=table_alias or self.resource_name, include_deleted=include_deleted)

    def filter_demo_rows(self, rows: Iterable[dict[str, Any]], *, include_deleted: bool = False) -> list[dict[str, Any]]:
        return filter_visible_items(rows, self.ctx, include_deleted=include_deleted)
