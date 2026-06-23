"""V7.4 release governance dashboard service.

V7.3 made config changes searchable, comparable, and rollbackable. V7.4 turns
feature flags and rollout rules into a SaaS release governance dashboard:
coverage, rollout percentage, role exposure, audit volume, rollback count, and
release status are summarized per feature flag.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List

from src.core.context import UserContext
from src.repositories.sqlite_repository import connect, loads
from src.services.v71_tenant_config_service import ensure_v71_tenant_config_tables, tenant_config_summary
from src.services.v73_config_audit_service import config_audit_summary

V74_RELEASE_GOVERNANCE_VERSION = "7.4.0"


def ensure_release_governance_tables() -> None:
    """Release governance currently reads V7 config and audit tables."""
    ensure_v71_tenant_config_tables()


def _load_flags() -> List[Dict[str, Any]]:
    ensure_release_governance_tables()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM feature_flags_v7 ORDER BY flag_key ASC").fetchall()
    flags = []
    for row in rows:
        payload = loads(row["payload"])
        payload.update({"flagKey": row["flag_key"], "name": row["name"], "enabled": bool(row["enabled"]), "stage": row["stage"]})
        flags.append(payload)
    return flags


def _load_rollout_rules() -> List[Dict[str, Any]]:
    ensure_release_governance_tables()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM feature_rollout_rules_v7 ORDER BY flag_key ASC, percentage DESC").fetchall()
    rules = []
    for row in rows:
        payload = loads(row["payload"])
        payload.update({"ruleId": row["rule_id"], "flagKey": row["flag_key"], "tenantId": row["tenant_id"], "orgId": row["org_id"], "roleIds": loads(row["role_ids"]), "percentage": int(row["percentage"] or 0), "status": row["status"]})
        rules.append(payload)
    return rules


def _load_audit_counts(ctx: UserContext) -> Dict[str, Dict[str, int]]:
    audit = config_audit_summary(ctx, limit=500)
    counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for item in audit.get("audits") or []:
        target = item.get("targetKey") or "unknown"
        counts[target][item.get("action") or "unknown"] += 1
    return {target: dict(actions) for target, actions in counts.items()}


def _release_status(flag: Dict[str, Any], rules: List[Dict[str, Any]], audit_counts: Dict[str, int]) -> str:
    if not flag.get("enabled"):
        return "paused"
    active_rules = [rule for rule in rules if rule.get("status") == "active"]
    max_percent = max([int(rule.get("percentage") or 0) for rule in active_rules], default=0)
    rollback_count = audit_counts.get("rollback_config_change", 0)
    if rollback_count > 0:
        return "rollback_watch"
    if max_percent >= 100:
        return "full_release"
    if max_percent > 0:
        return "gray_release"
    return "enabled_without_rollout"


def release_governance_summary(ctx: UserContext) -> Dict[str, Any]:
    """Return feature rollout health, coverage, and rollback metrics."""
    tenant_config = tenant_config_summary(ctx)
    flags = _load_flags()
    rollouts = _load_rollout_rules()
    audit_counts = _load_audit_counts(ctx)
    rules_by_flag: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for rule in rollouts:
        rules_by_flag[rule.get("flagKey")].append(rule)
    release_items = []
    status_counts: Dict[str, int] = defaultdict(int)
    stage_counts: Dict[str, int] = defaultdict(int)
    role_coverage: Dict[str, int] = defaultdict(int)
    rollback_total = 0
    for flag in flags:
        flag_key = flag.get("flagKey")
        matched_rules = rules_by_flag.get(flag_key, [])
        active_rules = [rule for rule in matched_rules if rule.get("status") == "active"]
        roles = sorted({role for rule in active_rules for role in (rule.get("roleIds") or [])} or set(flag.get("allowedRoles") or []))
        max_percent = max([int(rule.get("percentage") or 0) for rule in active_rules], default=100 if flag.get("enabled") else 0)
        counts = audit_counts.get(flag_key, {})
        rollback_count = counts.get("rollback_config_change", 0)
        rollback_total += rollback_count
        status = _release_status(flag, matched_rules, counts)
        status_counts[status] += 1
        stage_counts[flag.get("stage") or "unknown"] += 1
        for role in roles:
            role_coverage[role] += 1
        release_items.append({
            "flagKey": flag_key,
            "name": flag.get("name"),
            "enabled": bool(flag.get("enabled")),
            "stage": flag.get("stage"),
            "allowedRoles": flag.get("allowedRoles") or [],
            "activeRoles": roles,
            "rolloutPercentage": max_percent,
            "ruleCount": len(matched_rules),
            "activeRuleCount": len(active_rules),
            "auditCounts": counts,
            "rollbackCount": rollback_count,
            "releaseStatus": status,
            "governanceNote": "回滚后观察" if status == "rollback_watch" else "全量开放" if status == "full_release" else "灰度中" if status == "gray_release" else "暂停或待配置",
        })
    return {
        "version": V74_RELEASE_GOVERNANCE_VERSION,
        "tenantId": ctx.tenant_id,
        "orgId": ctx.org_id,
        "roleId": ctx.role_id,
        "canManageRelease": ctx.role_id in {"owner", "manager"},
        "canRollback": ctx.role_id in {"owner", "manager"},
        "summary": {
            "featureCount": len(flags),
            "enabledCount": sum(1 for flag in flags if flag.get("enabled")),
            "rolloutRuleCount": len(rollouts),
            "rollbackCount": rollback_total,
            "enabledForContextCount": tenant_config.get("enabledForContextCount", 0),
        },
        "statusCounts": dict(status_counts),
        "stageCounts": dict(stage_counts),
        "roleCoverage": dict(role_coverage),
        "releaseItems": release_items,
        "rule": "V7.4 发布治理看板按功能开关汇总启用率、灰度比例、角色覆盖、审计量和回滚次数。",
    }
