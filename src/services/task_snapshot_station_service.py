"""V13.3 Task Snapshot Station service.

Task Snapshot is the formal decision package between Agent judgment and task pool.
It does not directly create visible tasks. It records why a task should be created,
observed, ignored as noise, or routed to manager review.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List

from src.repositories.sqlite_repository import connect, ensure_columns

TASK_SNAPSHOT_STATION_VERSION = "13.3.0"
VALID_DECISIONS = {"create_task_snapshot", "manager_review_required", "observe_only", "ignore_noise"}
READY_DECISIONS = {"create_task_snapshot", "manager_review_required"}


def now_iso() -> str:
    return datetime.now().isoformat()


def make_snapshot_id() -> str:
    return f"TS-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"


def ensure_task_snapshot_tables() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS task_snapshots (
                task_snapshot_id TEXT PRIMARY KEY,
                handoff_id TEXT,
                data_version TEXT,
                entity_type TEXT,
                entity_id TEXT,
                decision TEXT NOT NULL,
                status TEXT NOT NULL,
                confidence REAL DEFAULT 0,
                trend_type TEXT,
                priority TEXT,
                task_type TEXT,
                action_type TEXT,
                need_manager_review INTEGER DEFAULT 0,
                signal_ref TEXT,
                rag_context TEXT,
                agent_judgment TEXT,
                task_plan TEXT,
                evidence_requirements TEXT,
                payload TEXT,
                task_pool_status TEXT,
                created_by TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        ensure_columns(
            conn,
            "task_snapshots",
            {
                "handoff_id": "TEXT",
                "data_version": "TEXT",
                "entity_type": "TEXT",
                "entity_id": "TEXT",
                "confidence": "REAL DEFAULT 0",
                "trend_type": "TEXT",
                "priority": "TEXT",
                "task_type": "TEXT",
                "action_type": "TEXT",
                "need_manager_review": "INTEGER DEFAULT 0",
                "signal_ref": "TEXT",
                "rag_context": "TEXT",
                "agent_judgment": "TEXT",
                "task_plan": "TEXT",
                "evidence_requirements": "TEXT",
                "payload": "TEXT",
                "task_pool_status": "TEXT",
                "created_by": "TEXT",
            },
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_task_snapshots_handoff ON task_snapshots(handoff_id, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_task_snapshots_version ON task_snapshots(data_version, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_task_snapshots_decision ON task_snapshots(decision, status, created_at)")
        conn.commit()


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False)


def _loads(value: str | None, fallback: Any) -> Any:
    try:
        return json.loads(value or "")
    except Exception:
        return fallback


def _normalize_decision(value: str | None) -> str:
    raw = str(value or "create_task_snapshot").strip()
    aliases = {
        "create_task": "create_task_snapshot",
        "create": "create_task_snapshot",
        "task": "create_task_snapshot",
        "manager_review": "manager_review_required",
        "review_required": "manager_review_required",
        "observe": "observe_only",
        "observation": "observe_only",
        "ignore": "ignore_noise",
        "noise": "ignore_noise",
    }
    decision = aliases.get(raw, raw)
    return decision if decision in VALID_DECISIONS else "observe_only"


def _snapshot_status(decision: str) -> str:
    if decision == "create_task_snapshot":
        return "snapshot_ready"
    if decision == "manager_review_required":
        return "manager_review_required"
    if decision == "ignore_noise":
        return "noise_ignored"
    return "observation_recorded"


def _row_to_snapshot(row: Any) -> Dict[str, Any]:
    return {
        "version": TASK_SNAPSHOT_STATION_VERSION,
        "taskSnapshotId": row["task_snapshot_id"],
        "handoffId": row["handoff_id"],
        "dataVersion": row["data_version"],
        "entityType": row["entity_type"],
        "entityId": row["entity_id"],
        "decision": row["decision"],
        "status": row["status"],
        "confidence": float(row["confidence"] or 0),
        "trendType": row["trend_type"],
        "priority": row["priority"],
        "taskType": row["task_type"],
        "actionType": row["action_type"],
        "needManagerReview": bool(row["need_manager_review"]),
        "signalRef": row["signal_ref"],
        "ragContext": _loads(row["rag_context"], {}),
        "agentJudgment": _loads(row["agent_judgment"], {}),
        "taskPlan": _loads(row["task_plan"], {}),
        "evidenceRequirements": _loads(row["evidence_requirements"], []),
        "payload": _loads(row["payload"], {}),
        "taskPoolStatus": row["task_pool_status"],
        "createdBy": row["created_by"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def _update_handoff_for_snapshot(snapshot: Dict[str, Any]) -> None:
    handoff_id = snapshot.get("handoffId")
    if not handoff_id:
        return
    decision = snapshot.get("decision")
    with connect() as conn:
        row = conn.execute("SELECT * FROM station_handoffs WHERE handoff_id = ?", (handoff_id,)).fetchone()
        if not row:
            return
        payload = {}
        try:
            payload = json.loads(row["payload"] or "{}")
        except Exception:
            payload = {}
        payload["taskSnapshot"] = {
            "taskSnapshotId": snapshot.get("taskSnapshotId"),
            "decision": decision,
            "status": snapshot.get("status"),
            "confidence": snapshot.get("confidence"),
            "rule": "V13.3：Agent判断结果已整理为任务快照；是否入池由后续task_pool_station处理。",
        }
        conn.execute(
            """
            UPDATE station_handoffs
            SET status = ?, decision_status = ?, output_ref = ?, task_snapshot_count = task_snapshot_count + 1,
                payload = ?, updated_at = ?
            WHERE handoff_id = ?
            """,
            (
                "task_snapshot_ready" if decision in READY_DECISIONS else "agent_judgment_recorded",
                decision,
                f"task_snapshot:{snapshot.get('taskSnapshotId')}",
                json.dumps(payload, ensure_ascii=False),
                now_iso(),
                handoff_id,
            ),
        )
        conn.commit()


def create_task_snapshot(body: Dict[str, Any] | None = None, *, created_by: str | None = None) -> Dict[str, Any]:
    body = body or {}
    ensure_task_snapshot_tables()
    decision = _normalize_decision(body.get("decision") or (body.get("agentJudgment") or {}).get("decision"))
    task_plan = body.get("taskPlan") if isinstance(body.get("taskPlan"), dict) else {}
    agent_judgment = body.get("agentJudgment") if isinstance(body.get("agentJudgment"), dict) else {}
    rag_context = body.get("ragContext") if isinstance(body.get("ragContext"), dict) else {}
    evidence = body.get("evidenceRequirements") or task_plan.get("evidenceRequirements") or []
    if not isinstance(evidence, list):
        evidence = [str(evidence)]
    confidence = body.get("confidence") if body.get("confidence") is not None else agent_judgment.get("confidence") or 0
    try:
        confidence_value = float(confidence)
    except Exception:
        confidence_value = 0.0
    confidence_value = max(0.0, min(1.0, confidence_value))
    snapshot_id = make_snapshot_id()
    created_at = now_iso()
    payload = {
        "version": TASK_SNAPSHOT_STATION_VERSION,
        "taskSnapshotId": snapshot_id,
        "handoffId": body.get("handoffId") or body.get("handoff_id"),
        "dataVersion": body.get("dataVersion") or body.get("data_version"),
        "decision": decision,
        "stationId": "task_snapshot_station",
        "source": body.get("source") or "agent_judgment_station",
        "systemFacts": body.get("systemFacts") or {},
        "ragContext": rag_context,
        "agentJudgment": agent_judgment,
        "taskPlan": task_plan,
        "directTaskCreationAllowed": False,
        "taskPoolStatus": "not_entered",
        "rule": "任务快照是进入任务生命周期前的标准判断结论包，不直接创建任务池任务。",
    }
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO task_snapshots (
                task_snapshot_id, handoff_id, data_version, entity_type, entity_id,
                decision, status, confidence, trend_type, priority, task_type,
                action_type, need_manager_review, signal_ref, rag_context,
                agent_judgment, task_plan, evidence_requirements, payload,
                task_pool_status, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot_id,
                body.get("handoffId") or body.get("handoff_id"),
                body.get("dataVersion") or body.get("data_version"),
                body.get("entityType") or task_plan.get("entityType") or "product",
                body.get("entityId") or task_plan.get("entityId") or body.get("productId"),
                decision,
                _snapshot_status(decision),
                confidence_value,
                body.get("trendType") or agent_judgment.get("trendType"),
                task_plan.get("priority") or body.get("priority") or "中",
                task_plan.get("taskType") or body.get("taskType") or "经营任务快照",
                task_plan.get("actionType") or body.get("actionType"),
                1 if decision == "manager_review_required" or bool(task_plan.get("needManagerReview")) else 0,
                body.get("signalRef") or body.get("signal_ref"),
                _json(rag_context),
                _json(agent_judgment),
                _json(task_plan),
                _json(evidence),
                _json(payload),
                "not_entered",
                created_by,
                created_at,
                created_at,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM task_snapshots WHERE task_snapshot_id = ?", (snapshot_id,)).fetchone()
    snapshot = _row_to_snapshot(row)
    _update_handoff_for_snapshot(snapshot)
    snapshot["rule"] = payload["rule"]
    return snapshot


def list_task_snapshots(data_version: str | None = None, handoff_id: str | None = None, limit: int = 50) -> Dict[str, Any]:
    ensure_task_snapshot_tables()
    with connect() as conn:
        if handoff_id:
            rows = conn.execute("SELECT * FROM task_snapshots WHERE handoff_id = ? ORDER BY created_at DESC LIMIT ?", (handoff_id, limit)).fetchall()
        elif data_version:
            rows = conn.execute("SELECT * FROM task_snapshots WHERE data_version = ? ORDER BY created_at DESC LIMIT ?", (data_version, limit)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM task_snapshots ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    items = [_row_to_snapshot(row) for row in rows]
    return {"version": TASK_SNAPSHOT_STATION_VERSION, "snapshots": items, "snapshotCount": len(items), "dataVersion": data_version, "handoffId": handoff_id}


def get_task_snapshot(task_snapshot_id: str) -> Dict[str, Any] | None:
    ensure_task_snapshot_tables()
    with connect() as conn:
        row = conn.execute("SELECT * FROM task_snapshots WHERE task_snapshot_id = ?", (task_snapshot_id,)).fetchone()
    return _row_to_snapshot(row) if row else None


def task_snapshot_summary(limit: int = 50) -> Dict[str, Any]:
    result = list_task_snapshots(limit=limit)
    items = result.get("snapshots") or []
    by_decision: Dict[str, int] = {}
    by_status: Dict[str, int] = {}
    for item in items:
        by_decision[item["decision"]] = by_decision.get(item["decision"], 0) + 1
        by_status[item["status"]] = by_status.get(item["status"], 0) + 1
    return {
        "version": TASK_SNAPSHOT_STATION_VERSION,
        "total": len(items),
        "byDecision": by_decision,
        "byStatus": by_status,
        "latest": items[0] if items else None,
        "items": items,
        "rule": "任务快照只承接Agent判断结论；进入任务池必须由后续task_pool_station处理。",
    }
