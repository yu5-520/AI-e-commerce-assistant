"""V7.2 tenant configuration console service.

V7.1 introduced tenant config, feature flags, and rollout evaluation. V7.2 adds
an operation console layer: owner / manager can update feature flags from the
product UI, owner can adjust rollout rules, and every change is audited.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

from src.core.context import UserContext
from src.repositories.sqlite_repository import connect, dumps
from src.services.v71_tenant_config_service import ensure_v71_tenant_config_tables, tenant_config_summary, upsert_feature_flag

V72_TENANT_CONFIG_CONSOLE_VERSION = "7.2.0"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}".upper()


def tenant_config_console_summary(ctx: UserContext) -> Dict[str, Any]:
    """Return tenant config summary plus console action permissions."""
    base = tenant_config_summary(ctx)
    base["version"] = V72_TENANT_CONFIG_CONSOLE_VERSION
    base["consoleActions"] = {
        "canToggleFeatureFlag": ctx.role_id in {"owner", "manager"},
        "canUpdateRollout": ctx.role_id == "owner",
        "canViewAudit": ctx.role_id in {"owner", "manager", "finance"},
        "rule": "V7.2 前端可操作功能开关；灰度规则只允许老板调整。",
    }
    base["rule"] = "V7.2 租户配置中心支持前端启用、暂停和灰度配置，所有变更进入配置审计。"
    return base


def set_feature_flag_status(flag_key: str, body: Dict[str, Any], ctx: UserContext) -> Dict[str, Any]:
    """Update a feature flag from the config console."""
    if ctx.role_id not in {"owner", "manager"}:
        raise PermissionError("Only owner or manager can change feature flags.")
    normalized = {
        "name": body.get("name") or flag_key,
        "enabled": bool(body.get("enabled")),
        "stage": body.get("stage") or "beta",
        "allowedRoles": body.get("allowedRoles") or body.get("allowed_roles") or [],
    }
    result = upsert_feature_flag(flag_key, normalized, ctx)
    result["version"] = V72_TENANT_CONFIG_CONSOLE_VERSION
    result["consoleMode"] = "feature_flag_update"
    return result


def upsert_rollout_rule(flag_key: str, body: Dict[str, Any], ctx: UserContext) -> Dict[str, Any]:
    """Create or update rollout rule for a feature flag. Owner only."""
    if ctx.role_id != "owner":
        raise PermissionError("Only owner can update rollout rules.")
    ensure_v71_tenant_config_tables()
    now = now_iso()
    rule_id = body.get("ruleId") or body.get("rule_id") or f"ROLLOUT_{flag_key.upper()}_{ctx.tenant_id.upper()}"
    role_ids = body.get("roleIds") or body.get("role_ids") or ["owner", "manager"]
    percentage = int(body.get("percentage") if body.get("percentage") is not None else 100)
    percentage = max(0, min(100, percentage))
    status = body.get("status") or "active"
    payload = {
        "version": V72_TENANT_CONFIG_CONSOLE_VERSION,
        "ruleId": rule_id,
        "flagKey": flag_key,
        "tenantId": body.get("tenantId") or body.get("tenant_id") or ctx.tenant_id,
        "orgId": body.get("orgId") or body.get("org_id") or ctx.org_id,
        "roleIds": role_ids,
        "percentage": percentage,
        "status": status,
        "rule": body.get("rule") or "V7.2 前端灰度规则更新。",
        "updatedBy": ctx.user_id,
        "updatedAt": now,
    }
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO feature_rollout_rules_v7 (
                rule_id, flag_key, tenant_id, org_id, role_ids, percentage, status, payload, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM feature_rollout_rules_v7 WHERE rule_id = ?), ?), ?)
            """,
            (rule_id, flag_key, payload["tenantId"], payload["orgId"], dumps(role_ids), percentage, status, dumps(payload), rule_id, now, now),
        )
        conn.execute(
            """
            INSERT INTO tenant_config_audit_v7 (audit_id, tenant_id, org_id, action, target_key, actor_user_id, payload, created_at)
            VALUES (?, ?, ?, 'upsert_rollout_rule', ?, ?, ?, ?)
            """,
            (make_id("TCFG"), ctx.tenant_id, ctx.org_id, flag_key, ctx.user_id, dumps(payload), now),
        )
        conn.commit()
    return {"version": V72_TENANT_CONFIG_CONSOLE_VERSION, "rolloutRule": payload, "audit": {"action": "upsert_rollout_rule", "actorUserId": ctx.user_id, "createdAt": now}}
