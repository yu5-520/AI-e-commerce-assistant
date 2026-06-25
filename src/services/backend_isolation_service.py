"""Backend account and data-scope isolation guards.

V11.4 adds a production safety gate without breaking the demo runtime:

- Demo mode may still use X-Mock-User-Id for MVP role testing.
- Production mode must not trust frontend supplied mock identity headers.
- Imported rows missing tenant/org/store ownership are treated as quarantined and
  must not enter business projections when strict data scope is enabled.
"""

from __future__ import annotations

import os
from typing import Any, Mapping

DEFAULT_TENANT_ID = os.getenv("DEFAULT_TENANT_ID", "tenant_demo")
DEFAULT_ORG_ID = os.getenv("DEFAULT_ORG_ID", "org_demo")
TENANT_HEADER = "x-tenant-id"
ORG_HEADER = "x-org-id"
MOCK_USER_HEADERS = ("x-mock-user-id", "X-Mock-User-Id")
TRUSTED_USER_HEADERS = ("x-auth-user-id", "x-user-id", "X-Auth-User-Id", "X-User-Id")
TRUTHY = {"1", "true", "yes", "on", "strict", "production"}


def production_mode() -> bool:
    return os.getenv("APP_ENV", "demo").strip().lower() == "production"


def strict_data_scope_enabled() -> bool:
    raw = os.getenv("STRICT_DATA_SCOPE")
    if raw is None:
        return production_mode()
    return raw.strip().lower() in TRUTHY


def _headers(headers: Mapping[str, str] | None) -> Mapping[str, str]:
    return headers or {}


def header_value(headers: Mapping[str, str] | None, *names: str, default: str | None = None) -> str | None:
    source = _headers(headers)
    for name in names:
        if source.get(name):
            return str(source.get(name))
        lower = name.lower()
        title = name.title()
        upper = name.upper()
        for candidate in (lower, title, upper):
            if source.get(candidate):
                return str(source.get(candidate))
    return default


def mock_user_header_value(headers: Mapping[str, str] | None) -> str | None:
    return header_value(headers, *MOCK_USER_HEADERS)


def trusted_user_header_value(headers: Mapping[str, str] | None) -> str | None:
    return header_value(headers, *TRUSTED_USER_HEADERS)


def request_tenant_id(headers: Mapping[str, str] | None) -> str:
    return header_value(headers, TENANT_HEADER, default=DEFAULT_TENANT_ID) or DEFAULT_TENANT_ID


def request_org_id(headers: Mapping[str, str] | None) -> str:
    return header_value(headers, ORG_HEADER, default=DEFAULT_ORG_ID) or DEFAULT_ORG_ID


def row_scope_value(row: Mapping[str, Any], *names: str) -> str | None:
    for name in names:
        value = row.get(name)
        if value not in {None, ""}:
            return str(value).strip()
    return None


def row_tenant_id(row: Mapping[str, Any]) -> str | None:
    return row_scope_value(row, "tenantId", "tenant_id", "租户ID", "租户id")


def row_org_id(row: Mapping[str, Any]) -> str | None:
    return row_scope_value(row, "orgId", "org_id", "组织ID", "组织id", "经营单元ID", "经营单元id")


def row_store_id(row: Mapping[str, Any]) -> str | None:
    return row_scope_value(row, "storeId", "store_id", "店铺ID", "店铺id", "店铺编号", "店铺编码")


def row_scope_status(row: Mapping[str, Any], *, tenant_id: str = DEFAULT_TENANT_ID, org_id: str = DEFAULT_ORG_ID, store_id: str | None = None, require_store: bool = False) -> dict[str, Any]:
    """Return an auditable row scope decision.

    In demo mode, callers may use this as diagnostics. In strict mode, rows with
    invalid status must be quarantined instead of projected into modules.
    """
    row_tenant = row_tenant_id(row)
    row_org = row_org_id(row)
    row_store = store_id or row_store_id(row)
    missing: list[str] = []
    if not row_tenant:
        missing.append("tenant_id")
    if not row_org:
        missing.append("org_id")
    if require_store and not row_store:
        missing.append("store_id")
    errors: list[str] = []
    if row_tenant and row_tenant != tenant_id:
        errors.append("tenant_mismatch")
    if row_org and row_org != org_id:
        errors.append("org_mismatch")
    status = "ok" if not missing and not errors else "quarantine"
    return {
        "status": status,
        "tenantId": row_tenant,
        "orgId": row_org,
        "storeId": row_store,
        "missing": missing,
        "errors": errors,
        "strict": strict_data_scope_enabled(),
    }


def isolation_runtime_summary() -> dict[str, Any]:
    return {
        "version": "11.4.0",
        "appEnv": os.getenv("APP_ENV", "demo"),
        "productionMode": production_mode(),
        "strictDataScope": strict_data_scope_enabled(),
        "demoMockIdentityAllowed": not production_mode(),
        "identityRule": "production ignores X-Mock-User-Id and requires trusted auth identity headers",
        "dataRule": "strict mode quarantines rows missing tenant_id/org_id/store_id ownership before business projection",
    }
