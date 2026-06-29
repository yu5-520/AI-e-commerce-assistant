"""V12.13 pipeline station gate service.

The main data flow is a one-way station chain, not a page-triggered full
recalculation loop. Every station writes a gate record keyed by tenant,
data_version, stage and input_hash. Later readers reuse finished outputs instead
of pulling upstream raw reports again.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List

from src.repositories.sqlite_repository import connect, ensure_columns

PIPELINE_GATE_VERSION = "12.13.0"

PIPELINE_STAGES = [
    "import_uploaded",
    "report_parsed",
    "metric_facts_ready",
    "operating_objects_ready",
    "operating_unit_snapshot_ready",
    "task_signal_ready",
    "task_agent_enhanced",
    "operator_evidence_submitted",
    "system_auto_recap_completed",
    "rag_candidate_ready",
]


def now_iso() -> str:
    return datetime.now().isoformat()


def stable_hash(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def ensure_pipeline_tables() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pipeline_stage_gates (
                gate_key TEXT PRIMARY KEY,
                tenant_id TEXT,
                user_id TEXT,
                data_version TEXT,
                stage TEXT NOT NULL,
                status TEXT NOT NULL,
                input_hash TEXT,
                output_hash TEXT,
                upstream_stage TEXT,
                output_ref TEXT,
                payload TEXT,
                error_message TEXT,
                started_at TEXT,
                finished_at TEXT,
                updated_at TEXT NOT NULL
            )
            """
        )
        ensure_columns(
            conn,
            "pipeline_stage_gates",
            {
                "tenant_id": "TEXT",
                "user_id": "TEXT",
                "data_version": "TEXT",
                "input_hash": "TEXT",
                "output_hash": "TEXT",
                "upstream_stage": "TEXT",
                "output_ref": "TEXT",
                "payload": "TEXT",
                "error_message": "TEXT",
                "started_at": "TEXT",
                "finished_at": "TEXT",
            },
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_stage_gates_data_stage ON pipeline_stage_gates(data_version, stage, status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_stage_gates_user ON pipeline_stage_gates(user_id, data_version)")
        conn.commit()


def gate_key(*, data_version: str | None, stage: str, input_hash: str | None = None, tenant_id: str | None = None, user_id: str | None = None) -> str:
    return "|".join([tenant_id or "default", user_id or "system", data_version or "latest", stage, input_hash or "nohash"])


def get_stage_gate(*, data_version: str | None, stage: str, input_hash: str | None = None, tenant_id: str | None = None, user_id: str | None = None) -> Dict[str, Any] | None:
    ensure_pipeline_tables()
    key = gate_key(data_version=data_version, stage=stage, input_hash=input_hash, tenant_id=tenant_id, user_id=user_id)
    with connect() as conn:
        row = conn.execute("SELECT * FROM pipeline_stage_gates WHERE gate_key = ?", (key,)).fetchone()
    if not row:
        return None
    payload = {}
    try:
        payload = json.loads(row["payload"] or "{}")
    except Exception:
        payload = {}
    return {
        "version": PIPELINE_GATE_VERSION,
        "gateKey": row["gate_key"],
        "tenantId": row["tenant_id"],
        "userId": row["user_id"],
        "dataVersion": row["data_version"],
        "stage": row["stage"],
        "status": row["status"],
        "inputHash": row["input_hash"],
        "outputHash": row["output_hash"],
        "upstreamStage": row["upstream_stage"],
        "outputRef": row["output_ref"],
        "payload": payload,
        "errorMessage": row["error_message"],
        "startedAt": row["started_at"],
        "finishedAt": row["finished_at"],
        "updatedAt": row["updated_at"],
    }


def record_stage_gate(
    *,
    data_version: str | None,
    stage: str,
    status: str = "completed",
    input_payload: Any | None = None,
    output_payload: Any | None = None,
    tenant_id: str | None = None,
    user_id: str | None = None,
    upstream_stage: str | None = None,
    output_ref: str | None = None,
    error_message: str | None = None,
) -> Dict[str, Any]:
    ensure_pipeline_tables()
    input_hash = stable_hash(input_payload or {"stage": stage, "dataVersion": data_version})
    output_hash = stable_hash(output_payload or {"stage": stage, "status": status})
    key = gate_key(data_version=data_version, stage=stage, input_hash=input_hash, tenant_id=tenant_id, user_id=user_id)
    now = now_iso()
    started = now if status in {"running", "completed", "failed"} else None
    finished = now if status in {"completed", "skipped", "failed", "cached"} else None
    payload = {
        "version": PIPELINE_GATE_VERSION,
        "stage": stage,
        "input": input_payload or {},
        "output": output_payload or {},
        "rule": "V12.13：阶段完成后写阀门；页面读取只能复用标准产物，不能回头触发上游全量计算。",
    }
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO pipeline_stage_gates (
                gate_key, tenant_id, user_id, data_version, stage, status, input_hash, output_hash,
                upstream_stage, output_ref, payload, error_message, started_at, finished_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                key,
                tenant_id,
                user_id,
                data_version,
                stage,
                status,
                input_hash,
                output_hash,
                upstream_stage,
                output_ref,
                json.dumps(payload, ensure_ascii=False),
                error_message,
                started,
                finished,
                now,
            ),
        )
        conn.commit()
    return get_stage_gate(data_version=data_version, stage=stage, input_hash=input_hash, tenant_id=tenant_id, user_id=user_id) or {"version": PIPELINE_GATE_VERSION, "status": status, "stage": stage}


def stage_summary(data_version: str | None = None, user_id: str | None = None, limit: int = 80) -> Dict[str, Any]:
    ensure_pipeline_tables()
    where: List[str] = []
    params: List[Any] = []
    if data_version:
        where.append("data_version = ?")
        params.append(data_version)
    if user_id:
        where.append("user_id = ?")
        params.append(user_id)
    sql = "SELECT * FROM pipeline_stage_gates"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY updated_at DESC LIMIT ?"
    params.append(limit)
    with connect() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
    gates = []
    for row in rows:
        gates.append({
            "gateKey": row["gate_key"],
            "dataVersion": row["data_version"],
            "stage": row["stage"],
            "status": row["status"],
            "inputHash": row["input_hash"],
            "outputHash": row["output_hash"],
            "updatedAt": row["updated_at"],
            "outputRef": row["output_ref"],
            "errorMessage": row["error_message"],
        })
    completed = {gate["stage"] for gate in gates if gate.get("status") in {"completed", "cached"}}
    return {
        "version": PIPELINE_GATE_VERSION,
        "dataVersion": data_version,
        "knownStages": PIPELINE_STAGES,
        "completedStages": sorted(completed),
        "gateCount": len(gates),
        "gates": gates,
        "rule": "主流程为单向分站接力；只有RAG复盘回流进入学习循环。",
    }
