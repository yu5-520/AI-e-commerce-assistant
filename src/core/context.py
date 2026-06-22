"""Tenant-aware request context for the P0 SaaS runtime.

This module is intentionally dependency-light so it can be introduced without
breaking the current demo runtime. In production, the same UserContext contract
should be populated from JWT / Session claims instead of mock headers.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from fastapi import Request

from src.services.account_service import current_user, user_id_from_headers, visible_store_ids_for_user

DEFAULT_TENANT_ID = os.getenv("DEFAULT_TENANT_ID", "tenant_demo")
DEFAULT_ORG_ID = os.getenv("DEFAULT_ORG_ID", "org_demo")
TENANT_HEADER = "x-tenant-id"
ORG_HEADER = "x-org-id"


@dataclass(frozen=True)
class UserContext:
    """Canonical SaaS identity + data-scope object.

    P0 rule: handlers should depend on this object instead of manually reading
    tenant_id, user_id, role_id, or store scope from request headers.
    """

    tenant_id: str
    org_id: str
    user_id: str
    role_id: str
    role_name: str
    permissions: list[str] = field(default_factory=list)
    store_group_ids: list[str] = field(default_factory=list)
    store_ids: list[str] = field(default_factory=list)
    visible_modules: list[str] = field(default_factory=list)
    demo_mode: bool = True

    @property
    def is_owner(self) -> bool:
        return self.role_id == "owner"

    @property
    def is_manager(self) -> bool:
        return self.role_id == "manager"

    @property
    def is_operator(self) -> bool:
        return self.role_id == "operator"

    def can(self, permission: str) -> bool:
        return permission in set(self.permissions)

    def audit_meta(self) -> dict[str, Any]:
        return {
            "tenantId": self.tenant_id,
            "orgId": self.org_id,
            "userId": self.user_id,
            "roleId": self.role_id,
            "storeGroupIds": list(self.store_group_ids),
            "storeIds": list(self.store_ids),
            "demoMode": self.demo_mode,
        }

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _header_value(headers: Mapping[str, str] | None, name: str, default: str) -> str:
    headers = headers or {}
    return headers.get(name) or headers.get(name.title()) or headers.get(name.upper()) or default


def context_from_headers(headers: Mapping[str, str] | None = None) -> UserContext:
    """Build UserContext from demo headers.

    Production replacement point: verify JWT / session, load tenant membership,
    then return the same UserContext contract.
    """

    headers = headers or {}
    user_id = user_id_from_headers(headers)
    user = current_user(user_id)
    tenant_id = _header_value(headers, TENANT_HEADER, DEFAULT_TENANT_ID)
    org_id = _header_value(headers, ORG_HEADER, DEFAULT_ORG_ID)
    return UserContext(
        tenant_id=tenant_id,
        org_id=org_id,
        user_id=user.get("id", user_id),
        role_id=user.get("roleId", "observer"),
        role_name=user.get("roleName", "未知角色"),
        permissions=list(user.get("permissions") or []),
        store_group_ids=list(user.get("storeGroupIds") or []),
        store_ids=list(visible_store_ids_for_user(user.get("id"))),
        visible_modules=list(user.get("visibleModules") or []),
        demo_mode=os.getenv("APP_ENV", "demo") != "production",
    )


async def get_current_context(request: Request) -> UserContext:
    """FastAPI dependency used by P0 SaaS routes.

    Do not manually parse tenant/user scope inside handlers. Add this dependency
    and pass ctx into services/repositories.
    """

    return context_from_headers(request.headers)
