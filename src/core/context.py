"""Tenant-aware request context for the P0 SaaS runtime.

V12.2.8 keeps the production isolation model, but lets an ECS demo explicitly
allow mock identity with DEMO_ACCOUNT_SWITCH=true.  This is only for demo role
validation; production remains strict by default.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from fastapi import HTTPException, Request

from src.services.account_service import current_user, get_user, user_id_from_headers, visible_store_ids_for_user
from src.services.backend_isolation_service import (
    DEFAULT_ORG_ID,
    DEFAULT_TENANT_ID,
    demo_mock_identity_allowed,
    mock_user_header_value,
    production_mode,
    request_org_id,
    request_tenant_id,
    strict_data_scope_enabled,
    trusted_user_header_value,
)

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
    auth_source: str = "demo_mock_header"
    strict_scope: bool = False

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
            "authSource": self.auth_source,
            "strictScope": self.strict_scope,
        }

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _resolve_request_user(headers: Mapping[str, str]) -> tuple[str, str]:
    """Resolve user identity with different demo/production trust rules."""
    if production_mode() and not demo_mock_identity_allowed():
        if mock_user_header_value(headers):
            raise HTTPException(status_code=403, detail="X-Mock-User-Id is disabled in production")
        user_id = trusted_user_header_value(headers)
        if not user_id:
            raise HTTPException(status_code=401, detail="missing trusted auth identity")
        if not get_user(user_id):
            raise HTTPException(status_code=401, detail="unknown auth identity")
        return user_id, "trusted_auth_header"
    return user_id_from_headers(headers), "demo_mock_header"


def context_from_headers(headers: Mapping[str, str] | None = None) -> UserContext:
    """Build UserContext from request headers.

    Production replacement point: verify JWT / session, load tenant membership,
    then return the same UserContext contract. Do not read user_id directly from
    business handlers.
    """

    headers = headers or {}
    user_id, auth_source = _resolve_request_user(headers)
    user = current_user(user_id)
    tenant_id = request_tenant_id(headers)
    org_id = request_org_id(headers)
    if production_mode() and not demo_mock_identity_allowed():
        if tenant_id == DEFAULT_TENANT_ID and not headers.get(TENANT_HEADER):
            raise HTTPException(status_code=401, detail="missing tenant scope")
        if org_id == DEFAULT_ORG_ID and not headers.get(ORG_HEADER):
            raise HTTPException(status_code=401, detail="missing organization scope")
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
        demo_mode=demo_mock_identity_allowed(),
        auth_source=auth_source,
        strict_scope=strict_data_scope_enabled(),
    )


async def get_current_context(request: Request) -> UserContext:
    """FastAPI dependency used by P0 SaaS routes.

    Do not manually parse tenant/user scope inside handlers. Add this dependency
    and pass ctx into services/repositories.
    """
    return context_from_headers(request.headers)
