"""V7.5 release governance alert service.

V7.4 made release status measurable. V7.5 turns release risks into actionable
alerts and optional governance tasks: enabled features without rollout, rollback
watch, missing role coverage, and high audit churn are surfaced for owner / manager
follow-up.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from src.core.context import UserContext
from src.repositories.sqlite_repository import connect, dumps, loads
from src.services import module_task_service
from src.services.v74_release_governance_service import release_governance_summary

V75_RELEASE_ALERT_VERSION = "7.5.0"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}".upper()


def ensure_release_alert_tables() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS release_governance_alerts_v7 (
                alert_id TEXT PRIMARY KEY,
                flag_key TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                status TEXT NOT NULL,
                payload TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_release_alerts_flag_v7 ON release_governance_alerts_v7(flag_key, status, severity)")
        conn.commit()


def _alert_id(flag_key: str, alert_type: str) -> str:
    return f"RALERT_{flag_key}_{alert_type}".upper().replace("-", "_")


def _audit_total(item: Dict[str, Any]) -> int:
    return sum(int(value or 0) for value in (item.get("auditCounts") or {}).values())


def _build_alerts_from_release(release: Dict[str, Any]) -> List[Dict[str, Any]]:
    alerts: List[Dict[str, Any]] = []
    for item in release.get("releaseItems") or []:
        flag_key = str(item.get("flagKey") or "unknown")
        status = item.get("releaseStatus")
        roles = item.get("activeRoles") or []
        rollout = int(item.get("rolloutPercentage") or 0)
        rollback_count = int(item.get("rollbackCount") or 0)
        audit_total = _audit_total(item)
        if status == "enabled_without_rollout":
            alerts.append({"flagKey": flag_key, "alertType": "enabled_without_rollout", "severity": "高", "title": "功能已启用但缺少有效灰度规则", "suggestion": "补充 active 灰度规则，明确租户、角色和灰度比例。"})
        if status == "rollback_watch" or rollback_count > 0:
            alerts.append({"flagKey": flag_key, "alertType": "rollback_watch", "severity": "高", "title": "功能发生回滚，需要发布复核", "suggestion": "复查回滚原因、影响角色和下一次发布条件。"})
        if item.get("enabled") and not roles:
            alerts.append({"flagKey": flag_key, "alertType": "missing_role_coverage", "severity": "中", "title": "功能缺少角色覆盖", "suggestion": "设置 owner / manager / operator / finance 的可见范围。"})
        if status == "gray_release" and rollout >= 80:
            alerts.append({"flagKey": flag_key, "alertType": "near_full_rollout", "severity": "中", "title": "灰度比例接近全量", "suggestion": "全量前确认审计记录、回滚记录和角色覆盖。"})
        if audit_total >= 5:
            alerts.append({"flagKey": flag_key, "alertType": "high_audit_churn", "severity": "中", "title": "配置变更频繁", "suggestion": "复核近期配置变更是否存在反复启停或灰度震荡。"})
    return alerts


def _upsert_alert(alert: Dict[str, Any]) -> Dict[str, Any]:
    ensure_release_alert_tables()
    now = now_iso()
    alert_id = _alert_id(alert["flagKey"], alert["alertType"])
    payload = {**alert, "version": V75_RELEASE_ALERT_VERSION, "alertId": alert_id, "status": "open", "createdAt": now, "updatedAt": now}
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO release_governance_alerts_v7 (alert_id, flag_key, alert_type, severity, status, payload, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'open', ?, COALESCE((SELECT created_at FROM release_governance_alerts_v7 WHERE alert_id = ?), ?), ?)
            """,
            (alert_id, alert["flagKey"], alert["alertType"], alert["severity"], dumps(payload), alert_id, now, now),
        )
        conn.commit()
    return payload


def _task_payload(alert: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "title": f"发布治理：{alert.get('title')}",
        "task": f"处理功能 {alert.get('flagKey')} 的发布治理预警",
        "productId": alert.get("flagKey"),
        "entityType": "SaaS功能",
        "entityId": alert.get("alertId"),
        "priority": alert.get("severity") or "中",
        "riskDomain": "发布治理",
        "actionType": "治理复查",
        "source": "发布治理",
        "sourceModule": "发布治理",
        "sourceRoute": "release-governance",
        "taskLayer": "manager_dispatch",
        "visibleRoleIds": ["owner", "manager", "finance"],
        "deadline": "24小时内",
        "reason": alert.get("suggestion"),
        "judgmentTags": ["V7.5", alert.get("alertType"), alert.get("severity")],
        "sourceTrail": ["V7.4发布治理", "V7.5发布预警"],
        "agentJudgment": {"status": "release_governance_alert", "summary": alert.get("suggestion")},
    }


def generate_release_alerts(ctx: UserContext, create_tasks: bool = False) -> Dict[str, Any]:
    release = release_governance_summary(ctx)
    raw_alerts = _build_alerts_from_release(release)
    alerts = [_upsert_alert(item) for item in raw_alerts]
    created_tasks = []
    permission_note = "allowed"
    if create_tasks and ctx.role_id not in {"owner", "manager"}:
        create_tasks = False
        permission_note = "current role cannot create governance tasks"
    if create_tasks:
        for alert in alerts:
            if alert.get("severity") in {"高", "中"}:
                created_tasks.append(module_task_service.create_task(_task_payload(alert)))
    return {"version": V75_RELEASE_ALERT_VERSION, "roleId": ctx.role_id, "generatedCount": len(alerts), "createdTaskCount": len(created_tasks), "alerts": alerts, "createdTasks": created_tasks, "permissionNote": permission_note, "rule": "V7.5 将发布治理异常转成预警；老板/总管可生成治理任务。"}


def release_alert_summary(ctx: UserContext, limit: int = 100) -> Dict[str, Any]:
    ensure_release_alert_tables()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM release_governance_alerts_v7 ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
    alerts = [loads(row["payload"]) for row in rows]
    by_severity: Dict[str, int] = defaultdict(int)
    by_type: Dict[str, int] = defaultdict(int)
    for alert in alerts:
        by_severity[str(alert.get("severity") or "unknown")] += 1
        by_type[str(alert.get("alertType") or "unknown")] += 1
    return {"version": V75_RELEASE_ALERT_VERSION, "roleId": ctx.role_id, "alertCount": len(alerts), "bySeverity": dict(by_severity), "byType": dict(by_type), "alerts": alerts, "canGenerateTasks": ctx.role_id in {"owner", "manager"}, "rule": "发布治理预警用于发现灰度、回滚、角色覆盖和频繁变更问题。"}
