"""V7.3 configuration audit center service.

V7.2 made tenant configuration operable from the product UI. V7.3 turns those
changes into a governance workflow: list/search audit events, compare a change
with its previous state, and rollback a feature flag or rollout rule through an
audited action.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from src.core.context import UserContext
from src.repositories.sqlite_repository import connect, dumps, loads
from src.services.v71_tenant_config_service import ensure_v71_tenant_config_tables

V73_CONFIG_AUDIT_VERSION = "7.3.0"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}".upper()


def ensure_config_audit_center_tables() -> None:
    """Ensure the V7 tenant config audit tables exist."""
    ensure_v71_tenant_config_tables()


def _row_to_audit(row: Any) -> Dict[str, Any]:
    return {
        "auditId": row["audit_id"],
        "tenantId": row["tenant_id"],
        "orgId": row["org_id"],
        "action": row["action"],
        "targetKey": row["target_key"],
        "actorUserId": row["actor_user_id"],
        "payload": loads(row["payload"]),
        "createdAt": row["created_at"],
    }


def _fetch_audit(audit_id: str, ctx: UserContext) -> Dict[str, Any] | None:
    ensure_config_audit_center_tables()
    with connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM tenant_config_audit_v7
            WHERE audit_id = ? AND tenant_id = ? AND org_id = ?
            """,
            (audit_id, ctx.tenant_id, ctx.org_id),
        ).fetchone()
    return _row_to_audit(row) if row else None


def _previous_audit(target_key: str | None, created_at: str, ctx: UserContext) -> Dict[str, Any] | None:
    if not target_key:
        return None
    with connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM tenant_config_audit_v7
            WHERE tenant_id = ? AND org_id = ? AND target_key = ? AND created_at < ?
              AND action IN ('upsert_feature_flag', 'upsert_rollout_rule', 'rollback_config_change')
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (ctx.tenant_id, ctx.org_id, target_key, created_at),
        ).fetchone()
    return _row_to_audit(row) if row else None


def config_audit_summary(ctx: UserContext, action: str | None = None, target_key: str | None = None, limit: int = 50) -> Dict[str, Any]:
    """List/search tenant config audit events for current tenant/org."""
    ensure_config_audit_center_tables()
    filters: List[str] = ["tenant_id = ?", "org_id = ?"]
    params: List[Any] = [ctx.tenant_id, ctx.org_id]
    if action:
        filters.append("action = ?")
        params.append(action)
    if target_key:
        filters.append("target_key = ?")
        params.append(target_key)
    params.append(limit)
    with connect() as conn:
        rows = conn.execute(
            f"SELECT * FROM tenant_config_audit_v7 WHERE {' AND '.join(filters)} ORDER BY created_at DESC LIMIT ?",
            tuple(params),
        ).fetchall()
    audits = [_row_to_audit(row) for row in rows]
    by_action: Dict[str, int] = defaultdict(int)
    by_target: Dict[str, int] = defaultdict(int)
    for item in audits:
        by_action[str(item.get("action") or "unknown")] += 1
        by_target[str(item.get("targetKey") or "unknown")] += 1
    return {
        "version": V73_CONFIG_AUDIT_VERSION,
        "tenantId": ctx.tenant_id,
        "orgId": ctx.org_id,
        "roleId": ctx.role_id,
        "canRollback": ctx.role_id in {"owner", "manager"},
        "canCompare": ctx.role_id in {"owner", "manager", "finance"},
        "auditCount": len(audits),
        "byAction": dict(by_action),
        "byTarget": dict(by_target),
        "audits": audits,
        "rule": "V7.3 配置审计中心支持搜索、对比和回滚；回滚本身也必须写入审计。",
    }


def compare_config_audit(audit_id: str, ctx: UserContext) -> Dict[str, Any]:
    """Compare an audit event with the previous audited state for the same target."""
    if ctx.role_id not in {"owner", "manager", "finance"}:
        raise PermissionError("Only owner, manager, or finance can compare config audits.")
    audit = _fetch_audit(audit_id, ctx)
    if not audit:
        raise ValueError(f"config audit not found: {audit_id}")
    previous = _previous_audit(audit.get("targetKey"), audit.get("createdAt"), ctx)
    current_payload = audit.get("payload") or {}
    previous_payload = (previous or {}).get("payload") or {}
    changed_keys = sorted(set(current_payload.keys()) | set(previous_payload.keys()))
    diff = [
        {"key": key, "previous": previous_payload.get(key), "current": current_payload.get(key), "changed": previous_payload.get(key) != current_payload.get(key)}
        for key in changed_keys
    ]
    return {
        "version": V73_CONFIG_AUDIT_VERSION,
        "audit": audit,
        "previousAudit": previous,
        "diff": diff,
        "changedCount": sum(1 for item in diff if item["changed"]),
        "rule": "对比只展示差异，不直接修改配置。",
    }


def _restore_feature_flag(target_key: str, payload: Dict[str, Any]) -> None:
    now = now_iso()
    flag_key = payload.get("flagKey") or target_key
    name = payload.get("name") or flag_key
    enabled = bool(payload.get("enabled"))
    stage = payload.get("stage") or "beta"
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO feature_flags_v7 (flag_key, name, enabled, stage, payload, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM feature_flags_v7 WHERE flag_key = ?), ?), ?)
            """,
            (flag_key, name, 1 if enabled else 0, stage, dumps(payload), flag_key, now, now),
        )
        conn.commit()


def _restore_rollout_rule(target_key: str, payload: Dict[str, Any]) -> None:
    now = now_iso()
    rule_id = payload.get("ruleId") or f"ROLLOUT_{target_key}"
    flag_key = payload.get("flagKey") or target_key
    role_ids = payload.get("roleIds") or []
    percentage = int(payload.get("percentage") or 0)
    status = payload.get("status") or "paused"
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO feature_rollout_rules_v7 (
                rule_id, flag_key, tenant_id, org_id, role_ids, percentage, status, payload, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM feature_rollout_rules_v7 WHERE rule_id = ?), ?), ?)
            """,
            (rule_id, flag_key, payload.get("tenantId"), payload.get("orgId"), dumps(role_ids), percentage, status, dumps(payload), rule_id, now, now),
        )
        conn.commit()


def rollback_config_audit(audit_id: str, ctx: UserContext) -> Dict[str, Any]:
    """Rollback a feature flag or rollout rule to the previous audited payload."""
    if ctx.role_id not in {"owner", "manager"}:
        raise PermissionError("Only owner or manager can rollback config audits.")
    audit = _fetch_audit(audit_id, ctx)
    if not audit:
        raise ValueError(f"config audit not found: {audit_id}")
    previous = _previous_audit(audit.get("targetKey"), audit.get("createdAt"), ctx)
    if not previous:
        raise ValueError("No previous audit payload to rollback to.")
    previous_payload = previous.get("payload") or {}
    action = previous.get("action")
    target_key = str(audit.get("targetKey") or previous_payload.get("flagKey") or "unknown")
    if action == "upsert_rollout_rule":
        if ctx.role_id != "owner":
            raise PermissionError("Only owner can rollback rollout rules.")
        _restore_rollout_rule(target_key, previous_payload)
    else:
        _restore_feature_flag(target_key, previous_payload)
    now = now_iso()
    rollback_payload = {
        "version": V73_CONFIG_AUDIT_VERSION,
        "rollbackAuditId": audit_id,
        "restoredFromAuditId": previous.get("auditId"),
        "targetKey": target_key,
        "restoredPayload": previous_payload,
        "actorUserId": ctx.user_id,
        "createdAt": now,
    }
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO tenant_config_audit_v7 (audit_id, tenant_id, org_id, action, target_key, actor_user_id, payload, created_at)
            VALUES (?, ?, ?, 'rollback_config_change', ?, ?, ?, ?)
            """,
            (make_id("TCFG"), ctx.tenant_id, ctx.org_id, target_key, ctx.user_id, dumps(rollback_payload), now),
        )
        conn.commit()
    return {
        "version": V73_CONFIG_AUDIT_VERSION,
        "status": "rolled_back",
        "rollback": rollback_payload,
        "sourceAudit": audit,
        "restoredAudit": previous,
        "rule": "回滚已写入审计，不会静默覆盖配置。",
    }
