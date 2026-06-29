"""V14.4 task storage consistency helpers."""

from __future__ import annotations

from typing import Any, Dict, List

from src.repositories.sqlite_repository import connect, dumps, loads
from src.services.agent_judgment_station_service import materialize_task_snapshots_from_judgments
from src.services.task_pool_station_service import sync_ready_task_snapshots
from src.services.task_snapshot_station_service import get_task_snapshot

TASK_STORAGE_CONSISTENCY_VERSION = "14.4.0"
TASK_DECISIONS = {"create_task_snapshot", "manager_review_required", "data_gap_required"}


def _row(row: Any) -> Dict[str, Any]:
    payload = loads(row["payload"])
    return {**payload, "judgmentId": row["judgment_id"], "dataVersion": row["data_version"], "signalId": row["signal_id"], "decision": row["decision"], "status": row["status"]}


def _snapshot_exists(item: Dict[str, Any]) -> bool:
    snapshot_id = item.get("taskSnapshotId")
    if snapshot_id and get_task_snapshot(str(snapshot_id)):
        return True
    signal_id = item.get("signalId")
    if not signal_id:
        return False
    with connect() as conn:
        row = conn.execute("SELECT task_snapshot_id FROM task_snapshots WHERE signal_ref = ? ORDER BY created_at DESC LIMIT 1", (signal_id,)).fetchone()
    return bool(row)


def storage_consistency_summary(data_version: str | None = None) -> Dict[str, Any]:
    params: List[Any] = []
    where = "WHERE decision IN ('create_task_snapshot','manager_review_required','data_gap_required')"
    if data_version:
        where += " AND data_version = ?"
        params.append(data_version)
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM agent_judgments_v14 {where} ORDER BY created_at DESC LIMIT 500", params).fetchall()
        snapshot_count = conn.execute("SELECT COUNT(*) AS c FROM task_snapshots").fetchone()["c"]
        pool_count = conn.execute("SELECT COUNT(*) AS c FROM task_pool_entries").fetchone()["c"]
    missing = []
    for row in rows:
        item = _row(row)
        if item.get("status") == "task_snapshot_created" and not _snapshot_exists(item):
            missing.append({"judgmentId": item.get("judgmentId"), "signalId": item.get("signalId"), "decision": item.get("decision")})
    return {"version": TASK_STORAGE_CONSISTENCY_VERSION, "dataVersion": data_version, "taskJudgmentCount": len(rows), "taskSnapshotCount": snapshot_count, "taskPoolEntryCount": pool_count, "danglingJudgmentCount": len(missing), "danglingJudgments": missing[:50], "status": "failed" if missing else "passed"}


def reconcile_task_storage(data_version: str | None = None, *, created_by: str | None = None, limit: int = 200) -> Dict[str, Any]:
    summary = storage_consistency_summary(data_version=data_version)
    reset_count = 0
    if summary.get("danglingJudgmentCount"):
        ids = [item["judgmentId"] for item in summary.get("danglingJudgments") or []]
        with connect() as conn:
            for judgment_id in ids:
                row = conn.execute("SELECT payload FROM agent_judgments_v14 WHERE judgment_id = ?", (judgment_id,)).fetchone()
                payload = loads(row["payload"]) if row else {}
                payload["taskSnapshotId"] = None
                payload["storageReconciled"] = True
                conn.execute("UPDATE agent_judgments_v14 SET status = ?, payload = ?, updated_at = datetime('now') WHERE judgment_id = ?", ("pending_task_snapshot", dumps(payload), judgment_id))
                reset_count += 1
            conn.commit()
    snapshots = materialize_task_snapshots_from_judgments(data_version=data_version, created_by=created_by, limit=limit)
    pool = sync_ready_task_snapshots(data_version=data_version, limit=limit, created_by=created_by)
    return {"version": TASK_STORAGE_CONSISTENCY_VERSION, "dataVersion": data_version, "resetJudgmentCount": reset_count, "taskSnapshotResult": snapshots, "taskPoolResult": pool, "after": storage_consistency_summary(data_version=data_version)}
