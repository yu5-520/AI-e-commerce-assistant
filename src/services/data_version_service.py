"""V3.1.1 data version rollback and import-record service.

Report imports create data versions. If a user uploads the wrong report, the
system should be able to soft-rollback the generated alerts from that version,
record who did it, and keep an auditable import history.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List
from uuid import uuid4

from src.repositories.sqlite_repository import connect, dumps, loads
from src.services.account_service import user_display
from src.services.report_alert_service import ACTIVE_ALERT_STATUSES, ensure_v3_tables, now_iso

ROLLBACK_VERSION = "3.1.1"
ROLLBACK_STATUSES = {"rolled_back", "rollback_pending"}


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}".upper()


def ensure_version_tables() -> None:
    ensure_v3_tables()
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS data_version_rollbacks (
                rollback_id TEXT PRIMARY KEY,
                data_version TEXT NOT NULL,
                snapshot_id TEXT,
                dataset_name TEXT,
                reason TEXT,
                operator_id TEXT,
                operator_name TEXT,
                affected_alert_count INTEGER NOT NULL,
                affected_task_count INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_data_version_rollbacks_version ON data_version_rollbacks(data_version, created_at)")
        conn.commit()


def _snapshot(row: Any) -> Dict[str, Any]:
    payload = loads(row["payload"])
    return payload or {
        "snapshotId": row["snapshot_id"],
        "importId": row["import_id"],
        "datasetName": row["dataset_name"],
        "dataVersion": row["data_version"],
        "rowCount": row["row_count"],
        "createdAt": row["created_at"],
    }


def _rollback_rows(limit: int = 200) -> List[Dict[str, Any]]:
    ensure_version_tables()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM data_version_rollbacks ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    result: List[Dict[str, Any]] = []
    for row in rows:
        payload = loads(row["payload"])
        result.append(payload or {
            "rollbackId": row["rollback_id"],
            "dataVersion": row["data_version"],
            "snapshotId": row["snapshot_id"],
            "datasetName": row["dataset_name"],
            "reason": row["reason"],
            "operatorId": row["operator_id"],
            "operatorName": row["operator_name"],
            "affectedAlertCount": row["affected_alert_count"],
            "affectedTaskCount": row["affected_task_count"],
            "status": row["status"],
            "createdAt": row["created_at"],
        })
    return result


def _latest_rollback_map() -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for item in _rollback_rows(500):
        result.setdefault(item.get("dataVersion"), item)
    return result


def list_import_records(limit: int = 50) -> Dict[str, Any]:
    ensure_version_tables()
    with connect() as conn:
        snapshots = conn.execute("SELECT * FROM data_snapshots ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        alert_rows = conn.execute(
            """
            SELECT data_version, status, COUNT(*) AS count, COUNT(task_id) AS task_count
            FROM alert_events
            GROUP BY data_version, status
            """
        ).fetchall()
    rollback_by_version = _latest_rollback_map()
    alert_summary: Dict[str, Dict[str, int]] = {}
    for row in alert_rows:
        version = row["data_version"]
        alert_summary.setdefault(version, {"alertCount": 0, "activeAlertCount": 0, "taskCount": 0, "rolledBackAlertCount": 0})
        alert_summary[version]["alertCount"] += int(row["count"] or 0)
        alert_summary[version]["taskCount"] += int(row["task_count"] or 0)
        if row["status"] in ACTIVE_ALERT_STATUSES:
            alert_summary[version]["activeAlertCount"] += int(row["count"] or 0)
        if row["status"] in ROLLBACK_STATUSES:
            alert_summary[version]["rolledBackAlertCount"] += int(row["count"] or 0)
    records: List[Dict[str, Any]] = []
    for row in snapshots:
        item = _snapshot(row)
        version = item.get("dataVersion") or row["data_version"]
        summary = alert_summary.get(version, {"alertCount": 0, "activeAlertCount": 0, "taskCount": 0, "rolledBackAlertCount": 0})
        rollback = rollback_by_version.get(version)
        status = "rolled_back" if rollback else "active"
        records.append({
            **item,
            "versionStatus": status,
            "rollback": rollback,
            "alertCount": summary["alertCount"],
            "activeAlertCount": summary["activeAlertCount"],
            "taskCount": summary["taskCount"],
            "rolledBackAlertCount": summary["rolledBackAlertCount"],
            "canRollback": status != "rolled_back" and summary["activeAlertCount"] > 0,
        })
    return {
        "version": ROLLBACK_VERSION,
        "total": len(records),
        "activeCount": len([item for item in records if item.get("versionStatus") == "active"]),
        "rolledBackCount": len([item for item in records if item.get("versionStatus") == "rolled_back"]),
        "records": records,
        "rollbacks": _rollback_rows(limit=limit),
    }


def rollback_data_version(data_version: str, *, operator_id: str | None = None, reason: str | None = None) -> Dict[str, Any]:
    ensure_version_tables()
    reason = reason or "上传报表有误，回滚该数据版本产生的预警。"
    operator_name = user_display(operator_id, "系统管理员")
    created_at = now_iso()
    with connect() as conn:
        snap = conn.execute("SELECT * FROM data_snapshots WHERE data_version = ? ORDER BY created_at DESC LIMIT 1", (data_version,)).fetchone()
        if not snap:
            raise ValueError(f"data version not found: {data_version}")
        rows = conn.execute("SELECT * FROM alert_events WHERE data_version = ?", (data_version,)).fetchall()
        active_rows = [row for row in rows if row["status"] in ACTIVE_ALERT_STATUSES]
        task_count = len([row for row in active_rows if row["task_id"]])
        for row in active_rows:
            payload = loads(row["payload"])
            if payload:
                payload = deepcopy(payload)
                payload["status"] = "rolled_back"
                payload["rollbackAt"] = created_at
                payload["rollbackReason"] = reason
                payload["rollbackOperatorId"] = operator_id
                payload["rollbackOperatorName"] = operator_name
            conn.execute(
                "UPDATE alert_events SET status = ?, payload = ?, updated_at = ? WHERE alert_id = ?",
                ("rolled_back", dumps(payload), created_at, row["alert_id"]),
            )
        rollback = {
            "rollbackId": make_id("ROLLBACK"),
            "version": ROLLBACK_VERSION,
            "dataVersion": data_version,
            "snapshotId": snap["snapshot_id"],
            "datasetName": snap["dataset_name"],
            "reason": reason,
            "operatorId": operator_id,
            "operatorName": operator_name,
            "affectedAlertCount": len(active_rows),
            "affectedTaskCount": task_count,
            "status": "rolled_back",
            "createdAt": created_at,
            "impact": ["该版本活跃预警已从看板移除", "已生成任务保留审计痕迹", "后续复盘仍可查看回滚记录"],
        }
        conn.execute(
            """
            INSERT OR REPLACE INTO data_version_rollbacks (
                rollback_id, data_version, snapshot_id, dataset_name, reason,
                operator_id, operator_name, affected_alert_count, affected_task_count,
                status, created_at, payload
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rollback["rollbackId"], data_version, rollback["snapshotId"], rollback["datasetName"], reason,
                operator_id, operator_name, rollback["affectedAlertCount"], rollback["affectedTaskCount"],
                rollback["status"], created_at, dumps(rollback),
            ),
        )
        conn.commit()
    return {"version": ROLLBACK_VERSION, "rollback": rollback, "records": list_import_records(limit=50)["records"]}
