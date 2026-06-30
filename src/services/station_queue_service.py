"""V14.6.2 station queue runtime with streaming task pool fast lane.

The product is split into three asynchronous systems:

1. import system: report rows -> operating objects -> metric facts -> operating snapshot
2. task generation system: product snapshot -> signal snapshot -> signal pool -> RAG -> Agent -> task snapshot
3. lifecycle system: task snapshot -> task pool -> receive/submit/review/recap

V14.6.2 changes the queue from async batch processing to streaming task intake:
once Agent produces task-worthy judgments, task_snapshot_station and task_pool_station
are inserted into a fast lane and consumed before lower-priority snapshot/signal work.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List
from uuid import uuid4

from src.repositories.sqlite_repository import connect, dumps, ensure_columns, loads
from src.services.pipeline_gate_service import record_stage_gate
from src.services.station_contract_service import run_station_contract

STATION_QUEUE_VERSION = "14.6.2"
TASK_GENERATION_SEQUENCE = [
    ("system_product_snapshot_station", "system_product_snapshot_ready"),
    ("product_signal_snapshot_station", "product_signal_snapshot_ready"),
    ("task_signal_station", "task_signal_ready"),
    ("rag_context_station", "rag_context_ready"),
    ("agent_judgment_station", "agent_judgment_ready"),
    ("task_snapshot_station", "task_snapshot_ready"),
    ("task_pool_station", "task_pool_ready"),
]
STATION_INDEX = {station: index for index, (station, _stage) in enumerate(TASK_GENERATION_SEQUENCE)}
STATION_PRIORITY = {
    "task_pool_station": 1,
    "task_snapshot_station": 5,
    "agent_judgment_station": 30,
    "rag_context_station": 40,
    "task_signal_station": 50,
    "product_signal_snapshot_station": 60,
    "system_product_snapshot_station": 70,
}
FAST_LANE_STATIONS = {"task_snapshot_station", "task_pool_station"}


def now_iso() -> str:
    return datetime.now().isoformat()


def _job_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:6].upper()}"


def _priority_for(station_id: str, default: int = 50) -> int:
    return int(STATION_PRIORITY.get(station_id, default))


def ensure_queue_tables() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pipeline_jobs (
                job_id TEXT PRIMARY KEY,
                system_type TEXT NOT NULL,
                tenant_id TEXT,
                actor_user_id TEXT,
                data_version TEXT,
                status TEXT NOT NULL,
                current_station TEXT,
                input_ref TEXT,
                output_ref TEXT,
                payload TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS station_queue (
                station_job_id TEXT PRIMARY KEY,
                parent_job_id TEXT NOT NULL,
                system_type TEXT NOT NULL,
                station_id TEXT NOT NULL,
                stage TEXT,
                data_version TEXT,
                status TEXT NOT NULL,
                priority INTEGER DEFAULT 50,
                input_ref TEXT,
                output_ref TEXT,
                payload TEXT,
                attempt_count INTEGER DEFAULT 0,
                max_attempts INTEGER DEFAULT 3,
                locked_by TEXT,
                locked_until TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        ensure_columns(conn, "pipeline_jobs", {"system_type": "TEXT", "tenant_id": "TEXT", "actor_user_id": "TEXT", "data_version": "TEXT", "status": "TEXT", "current_station": "TEXT", "input_ref": "TEXT", "output_ref": "TEXT", "payload": "TEXT", "error_message": "TEXT", "updated_at": "TEXT"})
        ensure_columns(conn, "station_queue", {"parent_job_id": "TEXT", "system_type": "TEXT", "station_id": "TEXT", "stage": "TEXT", "data_version": "TEXT", "status": "TEXT", "priority": "INTEGER DEFAULT 50", "input_ref": "TEXT", "output_ref": "TEXT", "payload": "TEXT", "attempt_count": "INTEGER DEFAULT 0", "max_attempts": "INTEGER DEFAULT 3", "locked_by": "TEXT", "locked_until": "TEXT", "error_message": "TEXT", "updated_at": "TEXT"})
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_jobs_status ON pipeline_jobs(system_type, status, updated_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_jobs_version ON pipeline_jobs(data_version, system_type, status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_station_queue_status ON station_queue(system_type, status, priority, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_station_queue_parent ON station_queue(parent_job_id, station_id, status)")
        for station_id, priority in STATION_PRIORITY.items():
            conn.execute("UPDATE station_queue SET priority = ? WHERE station_id = ? AND status IN ('queued', 'retry')", (priority, station_id))
        conn.commit()


def _row_to_job(row: Any) -> Dict[str, Any]:
    return {"version": STATION_QUEUE_VERSION, "jobId": row["job_id"], "systemType": row["system_type"], "tenantId": row["tenant_id"], "actorUserId": row["actor_user_id"], "dataVersion": row["data_version"], "status": row["status"], "currentStation": row["current_station"], "inputRef": row["input_ref"], "outputRef": row["output_ref"], "payload": loads(row["payload"]), "errorMessage": row["error_message"], "createdAt": row["created_at"], "updatedAt": row["updated_at"]}


def _row_to_station(row: Any) -> Dict[str, Any]:
    fast_lane = row["station_id"] in FAST_LANE_STATIONS or int(row["priority"] or 50) <= 5
    return {"version": STATION_QUEUE_VERSION, "stationJobId": row["station_job_id"], "parentJobId": row["parent_job_id"], "systemType": row["system_type"], "stationId": row["station_id"], "stage": row["stage"], "dataVersion": row["data_version"], "status": row["status"], "priority": row["priority"], "fastLane": fast_lane, "inputRef": row["input_ref"], "outputRef": row["output_ref"], "payload": loads(row["payload"]), "attemptCount": row["attempt_count"], "maxAttempts": row["max_attempts"], "lockedBy": row["locked_by"], "lockedUntil": row["locked_until"], "errorMessage": row["error_message"], "createdAt": row["created_at"], "updatedAt": row["updated_at"]}


def _insert_station_job(conn: Any, *, parent_job_id: str, system_type: str, station_id: str, stage: str, data_version: str | None, actor_user_id: str | None, input_ref: str | None, payload: Dict[str, Any] | None = None, priority: int | None = None) -> str:
    station_job_id = _job_id("SQ")
    body = dict(payload or {})
    body.setdefault("dataVersion", data_version)
    body.setdefault("userId", actor_user_id)
    body.setdefault("source", "station_queue")
    body["fastLane"] = station_id in FAST_LANE_STATIONS
    selected_priority = _priority_for(station_id, priority if priority is not None else 50)
    now = now_iso()
    conn.execute(
        """
        INSERT INTO station_queue (station_job_id, parent_job_id, system_type, station_id, stage, data_version, status, priority, input_ref, payload, attempt_count, max_attempts, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, 'queued', ?, ?, ?, 0, 3, ?, ?)
        """,
        (station_job_id, parent_job_id, system_type, station_id, stage, data_version, int(selected_priority), input_ref, dumps(body), now, now),
    )
    return station_job_id


def enqueue_task_generation(data_version: str | None, *, actor_user_id: str | None = None, input_ref: str | None = None, source: str = "import_completed", force: bool = True, priority: int = 70) -> Dict[str, Any]:
    ensure_queue_tables()
    now = now_iso()
    with connect() as conn:
        existing = conn.execute(
            """
            SELECT * FROM pipeline_jobs
            WHERE system_type = 'task_generation'
              AND COALESCE(data_version, '') = COALESCE(?, '')
              AND status IN ('queued', 'running')
            ORDER BY updated_at DESC LIMIT 1
            """,
            (data_version,),
        ).fetchone()
        if existing:
            return {"version": STATION_QUEUE_VERSION, "queued": False, "idempotentHit": True, "job": _row_to_job(existing), "rule": "Task generation job already queued or running for this data version."}
        job_id = _job_id("JOB-TASKGEN")
        first_station, first_stage = TASK_GENERATION_SEQUENCE[0]
        payload = {"version": STATION_QUEUE_VERSION, "source": source, "force": force, "dataVersion": data_version, "actorUserId": actor_user_id, "sequence": [station for station, _ in TASK_GENERATION_SEQUENCE], "boundary": "import system completed; task generation continues asynchronously", "streamingFastLane": True}
        conn.execute(
            """
            INSERT INTO pipeline_jobs (job_id, system_type, actor_user_id, data_version, status, current_station, input_ref, payload, created_at, updated_at)
            VALUES (?, 'task_generation', ?, ?, 'queued', ?, ?, ?, ?, ?)
            """,
            (job_id, actor_user_id, data_version, first_station, input_ref or f"operating_unit_snapshot:{data_version or 'latest'}", dumps(payload), now, now),
        )
        station_job_id = _insert_station_job(conn, parent_job_id=job_id, system_type="task_generation", station_id=first_station, stage=first_stage, data_version=data_version, actor_user_id=actor_user_id, input_ref=input_ref or f"operating_unit_snapshot:{data_version or 'latest'}", payload={"dataVersion": data_version, "userId": actor_user_id, "force": force, "source": source, "agentBatchSize": 20, "maxSignals": 20}, priority=priority)
        conn.commit()
        job = conn.execute("SELECT * FROM pipeline_jobs WHERE job_id = ?", (job_id,)).fetchone()
    record_stage_gate(data_version=data_version, stage="task_generation_queued", status="queued", input_payload={"source": source, "inputRef": input_ref}, output_payload={"jobId": job_id, "stationJobId": station_job_id, "streamingFastLane": True}, user_id=actor_user_id, upstream_stage="operating_unit_snapshot_ready", output_ref=f"pipeline_job:{job_id}")
    return {"version": STATION_QUEUE_VERSION, "queued": True, "job": _row_to_job(job), "stationJobId": station_job_id, "status": "queued", "rule": "Import returned; task generation is queued station-by-station with streaming fast lane."}


def _claim_next_station(system_type: str = "task_generation", *, worker_id: str = "manual-worker") -> Dict[str, Any] | None:
    ensure_queue_tables()
    now = now_iso()
    lock_until = (datetime.now() + timedelta(minutes=10)).isoformat()
    with connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM station_queue
            WHERE system_type = ?
              AND status IN ('queued', 'retry')
              AND (locked_until IS NULL OR locked_until < ?)
            ORDER BY priority ASC, created_at ASC
            LIMIT 1
            """,
            (system_type, now),
        ).fetchone()
        if not row:
            return None
        conn.execute("UPDATE station_queue SET status = 'running', locked_by = ?, locked_until = ?, attempt_count = attempt_count + 1, updated_at = ? WHERE station_job_id = ?", (worker_id, lock_until, now, row["station_job_id"]))
        conn.execute("UPDATE pipeline_jobs SET status = 'running', current_station = ?, updated_at = ? WHERE job_id = ?", (row["station_id"], now, row["parent_job_id"]))
        conn.commit()
        claimed = conn.execute("SELECT * FROM station_queue WHERE station_job_id = ?", (row["station_job_id"],)).fetchone()
    return _row_to_station(claimed)


def _next_station_for(station_id: str) -> tuple[str, str] | None:
    index = STATION_INDEX.get(station_id)
    if index is None or index + 1 >= len(TASK_GENERATION_SEQUENCE):
        return None
    return TASK_GENERATION_SEQUENCE[index + 1]


def _body_for_station(job: Dict[str, Any], station_job: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(station_job.get("payload") or {})
    payload.setdefault("dataVersion", station_job.get("dataVersion"))
    payload.setdefault("userId", job.get("actorUserId"))
    payload.setdefault("force", True)
    payload.setdefault("source", "station_queue_fast_lane" if station_job.get("fastLane") else "station_queue")
    payload.setdefault("maxSignals", 20)
    payload.setdefault("agentBatchSize", 20)
    payload.setdefault("limit", 20 if station_job.get("fastLane") else payload.get("limit", 20))
    input_ref = station_job.get("inputRef")
    station_id = station_job.get("stationId")
    if station_id == "product_signal_snapshot_station":
        payload.setdefault("productSnapshotRef", input_ref)
    elif station_id == "task_signal_station":
        payload.setdefault("productSignalSnapshotRef", input_ref)
    elif station_id == "rag_context_station":
        payload.setdefault("taskSignalRef", input_ref)
    elif station_id == "agent_judgment_station":
        payload.setdefault("ragContextRef", input_ref)
    elif station_id == "task_snapshot_station":
        payload.setdefault("agentJudgmentRef", input_ref)
    elif station_id == "task_pool_station":
        payload.setdefault("taskSnapshotRef", input_ref)
    return payload


def _output_ref(output: Dict[str, Any], station_id: str, data_version: str | None) -> str:
    return output.get("outputRef") or output.get("productSnapshotRef") or output.get("productSignalSnapshotRef") or output.get("taskSignalRef") or output.get("ragContextRef") or output.get("agentJudgmentRef") or f"{station_id}:{data_version or 'latest'}"


def _should_stream_to_next(station_id: str, output: Dict[str, Any]) -> bool:
    if station_id == "agent_judgment_station":
        return int(output.get("pendingTaskSnapshotCount") or 0) > 0 or int(output.get("judgmentCount") or 0) > 0
    if station_id == "task_snapshot_station":
        return int(output.get("taskSnapshotCount") or 0) > 0
    return True


def run_next_station_job(*, worker_id: str = "manual-worker", system_type: str = "task_generation") -> Dict[str, Any]:
    station_job = _claim_next_station(system_type=system_type, worker_id=worker_id)
    if not station_job:
        return {"version": STATION_QUEUE_VERSION, "ran": False, "status": "empty", "message": "No queued station job."}
    ensure_queue_tables()
    with connect() as conn:
        job_row = conn.execute("SELECT * FROM pipeline_jobs WHERE job_id = ?", (station_job["parentJobId"],)).fetchone()
    job = _row_to_job(job_row)
    body = _body_for_station(job, station_job)
    station_id = station_job["stationId"]
    try:
        run = run_station_contract(station_id, body, diagnostic=False)
        output = run.get("output") or {}
        output_ref = _output_ref(output, station_id, station_job.get("dataVersion"))
        now = now_iso()
        next_station = _next_station_for(station_id)
        inserted_next_id = None
        with connect() as conn:
            conn.execute("UPDATE station_queue SET status = 'completed', output_ref = ?, payload = ?, locked_until = NULL, error_message = NULL, updated_at = ? WHERE station_job_id = ?", (output_ref, dumps({"body": body, "stationRun": {"stationId": station_id, "status": run.get("status"), "outputRef": output_ref, "outputSummary": _compact_output(output)}, "fastLane": station_job.get("fastLane")}), now, station_job["stationJobId"]))
            if next_station and _should_stream_to_next(station_id, output):
                next_id, next_stage = next_station
                inserted_next_id = _insert_station_job(conn, parent_job_id=job["jobId"], system_type=job["systemType"], station_id=next_id, stage=next_stage, data_version=job.get("dataVersion"), actor_user_id=job.get("actorUserId"), input_ref=output_ref, payload={"dataVersion": job.get("dataVersion"), "userId": job.get("actorUserId"), "force": True, "source": "station_queue_fast_lane" if next_id in FAST_LANE_STATIONS else "station_queue", "maxSignals": 20, "agentBatchSize": 20, "fastLane": next_id in FAST_LANE_STATIONS}, priority=_priority_for(next_id))
                conn.execute("UPDATE pipeline_jobs SET status = 'running', current_station = ?, output_ref = ?, updated_at = ? WHERE job_id = ?", (next_id, output_ref, now, job["jobId"]))
            elif next_station:
                conn.execute("UPDATE pipeline_jobs SET status = 'running', current_station = ?, output_ref = ?, updated_at = ? WHERE job_id = ?", (next_station[0], output_ref, now, job["jobId"]))
            else:
                conn.execute("UPDATE pipeline_jobs SET status = 'completed', current_station = ?, output_ref = ?, updated_at = ? WHERE job_id = ?", (station_id, output_ref, now, job["jobId"]))
            conn.commit()
        record_stage_gate(data_version=job.get("dataVersion"), stage=station_job.get("stage") or station_id, status="completed", input_payload={"stationJobId": station_job["stationJobId"], "inputRef": station_job.get("inputRef"), "fastLane": station_job.get("fastLane")}, output_payload=_compact_output(output), user_id=job.get("actorUserId"), upstream_stage=None, output_ref=output_ref)
        return {"version": STATION_QUEUE_VERSION, "ran": True, "status": "completed", "stationJobId": station_job["stationJobId"], "stationId": station_id, "fastLane": station_job.get("fastLane"), "dataVersion": job.get("dataVersion"), "outputRef": output_ref, "nextStation": next_station[0] if next_station else None, "insertedNextStationJobId": inserted_next_id, "output": _compact_output(output), "rule": "V14.6.2 runs one station and prioritizes task_snapshot/task_pool fast lane."}
    except Exception as exc:
        now = now_iso()
        status = "failed"
        with connect() as conn:
            current = conn.execute("SELECT attempt_count, max_attempts FROM station_queue WHERE station_job_id = ?", (station_job["stationJobId"],)).fetchone()
            if current and int(current["attempt_count"] or 0) < int(current["max_attempts"] or 3):
                status = "retry"
            conn.execute("UPDATE station_queue SET status = ?, locked_until = NULL, error_message = ?, updated_at = ? WHERE station_job_id = ?", (status, str(exc), now, station_job["stationJobId"]))
            conn.execute("UPDATE pipeline_jobs SET status = ?, error_message = ?, updated_at = ? WHERE job_id = ?", ("failed" if status == "failed" else "running", str(exc), now, job["jobId"]))
            conn.commit()
        record_stage_gate(data_version=job.get("dataVersion"), stage=station_job.get("stage") or station_id, status=status, input_payload={"stationJobId": station_job["stationJobId"], "fastLane": station_job.get("fastLane")}, output_payload={}, user_id=job.get("actorUserId"), error_message=str(exc), output_ref=station_job.get("inputRef"))
        return {"version": STATION_QUEUE_VERSION, "ran": True, "status": status, "stationJobId": station_job["stationJobId"], "stationId": station_id, "fastLane": station_job.get("fastLane"), "error": str(exc), "rule": "Station failure is isolated to queue state; import request is not affected."}


def _compact_output(output: Dict[str, Any]) -> Dict[str, Any]:
    keys = ["version", "mode", "dataVersion", "productCount", "productSnapshotCount", "productSignalPackageCount", "productSignalCount", "signalCount", "matchedContextCount", "judgmentCount", "pendingTaskSnapshotCount", "taskSnapshotCount", "createdTaskCount", "outputRef", "productSnapshotRef", "productSignalSnapshotRef", "taskSignalRef", "ragContextRef", "agentJudgmentRef"]
    return {key: output.get(key) for key in keys if key in output and output.get(key) is not None}


def queue_summary(data_version: str | None = None, *, limit: int = 50) -> Dict[str, Any]:
    ensure_queue_tables()
    where: List[str] = []
    params: List[Any] = []
    if data_version:
        where.append("data_version = ?")
        params.append(data_version)
    clause = " WHERE " + " AND ".join(where) if where else ""
    with connect() as conn:
        jobs = conn.execute(f"SELECT * FROM pipeline_jobs{clause} ORDER BY updated_at DESC LIMIT ?", (*params, limit)).fetchall()
        stations = conn.execute(f"SELECT * FROM station_queue{clause} ORDER BY priority ASC, updated_at DESC LIMIT ?", (*params, limit)).fetchall()
    by_status: Dict[str, int] = {}
    by_station_status: Dict[str, int] = {}
    fast_lane_count = 0
    for row in stations:
        by_status[row["status"]] = by_status.get(row["status"], 0) + 1
        by_station_status[f"{row['station_id']}:{row['status']}"] = by_station_status.get(f"{row['station_id']}:{row['status']}", 0) + 1
        if row["station_id"] in FAST_LANE_STATIONS or int(row["priority"] or 50) <= 5:
            fast_lane_count += 1
    return {"version": STATION_QUEUE_VERSION, "mode": "streaming_fast_lane", "jobCount": len(jobs), "stationJobCount": len(stations), "fastLaneCount": fast_lane_count, "stationByStatus": by_status, "stationByStationStatus": by_station_status, "priorities": STATION_PRIORITY, "jobs": [_row_to_job(row) for row in jobs], "stationJobs": [_row_to_station(row) for row in stations], "rule": "V14.6.2 queue summary prioritizes mature task snapshots and task pool entries."}
