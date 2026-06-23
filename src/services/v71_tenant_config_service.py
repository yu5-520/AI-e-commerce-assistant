"""V7.1 tenant configuration, feature flag, and rollout service.

V7.0 introduced the SaaS control plane. V7.1 adds the first operational control
center: tenant-level configuration, role-aware feature flags, and simple rollout
rules. The purpose is to let SaaS capabilities be opened by tenant, role, and
version instead of hard-coding every feature into the frontend or backend.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from src.core.context import UserContext
from src.repositories.sqlite_repository import connect, dumps, loads

V71_TENANT_CONFIG_VERSION = "7.1.0"

DEFAULT_TENANT_CONFIG: Dict[str, Any] = {
    "plan": "demo_enterprise",
    "edition": "ai_operating_advisor_v7",
    "dataRetentionDays": 180,
    "defaultLocale": "zh-CN",
    "workflowMode": "closed_loop",
    "enabledModules": [
        "report_center",
        "trend_center",
        "risk_tasks",
        "approval_lifecycle",
        "execution_feedback",
        "execution_review",
        "rag_case_memory",
        "architecture_v7",
    ],
    "guardrails": {
        "highRiskDirectExecution": False,
        "agentMayInventMetrics": False,
        "approvalRequiredForHighRisk": True,
        "executionFeedbackRequired": True,
    },
}

DEFAULT_FEATURE_FLAGS: List[Dict[str, Any]] = [
    {"flagKey": "v7_control_plane", "name": "V7 SaaS 控制面", "enabled": True, "stage": "stable", "allowedRoles": ["owner", "manager", "operator", "finance"]},
    {"flagKey": "v71_tenant_config", "name": "V7.1 租户配置中心", "enabled": True, "stage": "stable", "allowedRoles": ["owner", "manager"]},
    {"flagKey": "report_import_unified", "name": "统一报表导入", "enabled": True, "stage": "stable", "allowedRoles": ["owner", "manager", "operator"]},
    {"flagKey": "trend_center_v6", "name": "动态趋势中心", "enabled": True, "stage": "stable", "allowedRoles": ["owner", "manager", "operator", "finance"]},
    {"flagKey": "risk_task_generation", "name": "风险分级任务", "enabled": True, "stage": "stable", "allowedRoles": ["owner", "manager", "operator", "finance"]},
    {"flagKey": "approval_frontend_actions", "name": "审批前端操作", "enabled": True, "stage": "stable", "allowedRoles": ["owner", "manager", "finance"]},
    {"flagKey": "execution_feedback", "name": "执行结果回写", "enabled": True, "stage": "stable", "allowedRoles": ["owner", "manager", "operator"]},
    {"flagKey": "execution_review_rag_memory", "name": "执行复盘与 RAG 案例沉淀", "enabled": True, "stage": "beta", "allowedRoles": ["owner", "manager", "finance"]},
    {"flagKey": "postgres_cutover_preview", "name": "PostgreSQL 主写切换检查", "enabled": False, "stage": "internal", "allowedRoles": ["owner"]},
    {"flagKey": "tenant_feature_rollout", "name": "租户灰度开关", "enabled": True, "stage": "stable", "allowedRoles": ["owner", "manager"]},
]

DEFAULT_ROLLOUT_RULES: List[Dict[str, Any]] = [
    {
        "ruleId": "ROLLOUT_DEMO_ALL_STABLE",
        "flagKey": "v7_control_plane",
        "tenantId": "tenant_demo",
        "orgId": "org_demo",
        "roleIds": ["owner", "manager", "operator", "finance"],
        "percentage": 100,
        "status": "active",
        "rule": "demo 租户默认开启 V7 控制面。",
    },
    {
        "ruleId": "ROLLOUT_MANAGER_CONFIG",
        "flagKey": "v71_tenant_config",
        "tenantId": "tenant_demo",
        "orgId": "org_demo",
        "roleIds": ["owner", "manager"],
        "percentage": 100,
        "status": "active",
        "rule": "配置中心只向老板和总管开放。",
    },
    {
        "ruleId": "ROLLOUT_POSTGRES_OWNER_ONLY",
        "flagKey": "postgres_cutover_preview",
        "tenantId": "tenant_demo",
        "orgId": "org_demo",
        "roleIds": ["owner"],
        "percentage": 0,
        "status": "paused",
        "rule": "生产主写切换默认不灰度，需老板手动开启。",
    },
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}".upper()


def ensure_v71_tenant_config_tables() -> None:
    """Create and seed tenant configuration / feature flag tables."""
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tenant_configs_v7 (
                tenant_id TEXT NOT NULL,
                org_id TEXT NOT NULL,
                config_key TEXT NOT NULL,
                config_value TEXT,
                status TEXT NOT NULL,
                updated_by TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (tenant_id, org_id, config_key)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS feature_flags_v7 (
                flag_key TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                enabled INTEGER DEFAULT 0,
                stage TEXT NOT NULL,
                payload TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS feature_rollout_rules_v7 (
                rule_id TEXT PRIMARY KEY,
                flag_key TEXT NOT NULL,
                tenant_id TEXT,
                org_id TEXT,
                role_ids TEXT,
                percentage INTEGER DEFAULT 0,
                status TEXT NOT NULL,
                payload TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tenant_config_audit_v7 (
                audit_id TEXT PRIMARY KEY,
                tenant_id TEXT,
                org_id TEXT,
                action TEXT NOT NULL,
                target_key TEXT,
                actor_user_id TEXT,
                payload TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        now = now_iso()
        conn.execute(
            """
            INSERT OR IGNORE INTO tenant_configs_v7 (tenant_id, org_id, config_key, config_value, status, updated_by, created_at, updated_at)
            VALUES (?, ?, 'default', ?, 'active', 'system_seed', ?, ?)
            """,
            ("tenant_demo", "org_demo", dumps(DEFAULT_TENANT_CONFIG), now, now),
        )
        for flag in DEFAULT_FEATURE_FLAGS:
            conn.execute(
                """
                INSERT OR IGNORE INTO feature_flags_v7 (flag_key, name, enabled, stage, payload, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (flag["flagKey"], flag["name"], 1 if flag.get("enabled") else 0, flag["stage"], dumps(flag), now, now),
            )
        for rule in DEFAULT_ROLLOUT_RULES:
            conn.execute(
                """
                INSERT OR IGNORE INTO feature_rollout_rules_v7 (rule_id, flag_key, tenant_id, org_id, role_ids, percentage, status, payload, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (rule["ruleId"], rule["flagKey"], rule.get("tenantId"), rule.get("orgId"), dumps(rule.get("roleIds") or []), int(rule.get("percentage") or 0), rule["status"], dumps(rule), now, now),
            )
        conn.commit()


def _load_tenant_config(ctx: UserContext) -> Dict[str, Any]:
    ensure_v71_tenant_config_tables()
    with connect() as conn:
        row = conn.execute(
            "SELECT config_value FROM tenant_configs_v7 WHERE tenant_id = ? AND org_id = ? AND config_key = 'default'",
            (ctx.tenant_id, ctx.org_id),
        ).fetchone()
    if row:
        return loads(row["config_value"])
    return {**DEFAULT_TENANT_CONFIG, "fallback": True}


def _load_flags() -> List[Dict[str, Any]]:
    ensure_v71_tenant_config_tables()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM feature_flags_v7 ORDER BY flag_key ASC").fetchall()
    result = []
    for row in rows:
        payload = loads(row["payload"])
        payload.update({"flagKey": row["flag_key"], "name": row["name"], "enabled": bool(row["enabled"]), "stage": row["stage"]})
        result.append(payload)
    return result


def _load_rollouts(ctx: UserContext) -> List[Dict[str, Any]]:
    ensure_v71_tenant_config_tables()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM feature_rollout_rules_v7
            WHERE status = 'active'
              AND (tenant_id IS NULL OR tenant_id = ?)
              AND (org_id IS NULL OR org_id = ?)
            ORDER BY flag_key ASC, percentage DESC
            """,
            (ctx.tenant_id, ctx.org_id),
        ).fetchall()
    rules = []
    for row in rows:
        payload = loads(row["payload"])
        payload.update({"ruleId": row["rule_id"], "flagKey": row["flag_key"], "percentage": int(row["percentage"] or 0), "status": row["status"], "roleIds": loads(row["role_ids"])})
        rules.append(payload)
    return rules


def _flag_enabled_for_context(flag: Dict[str, Any], rollouts: List[Dict[str, Any]], ctx: UserContext) -> Dict[str, Any]:
    allowed_roles = set(flag.get("allowedRoles") or [])
    role_allowed = not allowed_roles or ctx.role_id in allowed_roles
    matched_rules = [rule for rule in rollouts if rule.get("flagKey") == flag.get("flagKey") and (not rule.get("roleIds") or ctx.role_id in set(rule.get("roleIds") or []))]
    rollout_percentage = max([int(rule.get("percentage") or 0) for rule in matched_rules], default=100 if flag.get("enabled") else 0)
    enabled = bool(flag.get("enabled") and role_allowed and rollout_percentage > 0)
    reason = "enabled" if enabled else "disabled_by_flag_or_role_or_rollout"
    return {**flag, "enabledForContext": enabled, "roleAllowed": role_allowed, "rolloutPercentage": rollout_percentage, "matchedRuleIds": [rule.get("ruleId") for rule in matched_rules], "reason": reason}


def tenant_config_summary(ctx: UserContext) -> Dict[str, Any]:
    """Return tenant config, evaluated feature flags, and rollout rules for context."""
    config = _load_tenant_config(ctx)
    flags = _load_flags()
    rollouts = _load_rollouts(ctx)
    evaluated = [_flag_enabled_for_context(flag, rollouts, ctx) for flag in flags]
    by_stage: Dict[str, int] = defaultdict(int)
    for flag in evaluated:
        by_stage[str(flag.get("stage") or "unknown")] += 1
    return {
        "version": V71_TENANT_CONFIG_VERSION,
        "tenantId": ctx.tenant_id,
        "orgId": ctx.org_id,
        "roleId": ctx.role_id,
        "config": config,
        "featureFlagCount": len(evaluated),
        "enabledForContextCount": sum(1 for flag in evaluated if flag.get("enabledForContext")),
        "byStage": dict(by_stage),
        "featureFlags": evaluated,
        "rolloutRules": rollouts,
        "rule": "V7.1 通过租户配置、角色权限和灰度规则控制功能开放，不再把 SaaS 能力硬编码为全量开放。",
    }


def upsert_feature_flag(flag_key: str, body: Dict[str, Any], ctx: UserContext) -> Dict[str, Any]:
    """Create or update a feature flag and record an audit event."""
    ensure_v71_tenant_config_tables()
    now = now_iso()
    name = body.get("name") or flag_key
    enabled = bool(body.get("enabled"))
    stage = body.get("stage") or "beta"
    payload = {"flagKey": flag_key, "name": name, "enabled": enabled, "stage": stage, "allowedRoles": body.get("allowedRoles") or body.get("allowed_roles") or []}
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO feature_flags_v7 (flag_key, name, enabled, stage, payload, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM feature_flags_v7 WHERE flag_key = ?), ?), ?)
            """,
            (flag_key, name, 1 if enabled else 0, stage, dumps(payload), flag_key, now, now),
        )
        conn.execute(
            """
            INSERT INTO tenant_config_audit_v7 (audit_id, tenant_id, org_id, action, target_key, actor_user_id, payload, created_at)
            VALUES (?, ?, ?, 'upsert_feature_flag', ?, ?, ?, ?)
            """,
            (make_id("TCFG"), ctx.tenant_id, ctx.org_id, flag_key, ctx.user_id, dumps(payload), now),
        )
        conn.commit()
    return {"version": V71_TENANT_CONFIG_VERSION, "featureFlag": payload, "audit": {"action": "upsert_feature_flag", "actorUserId": ctx.user_id, "createdAt": now}}
