"""Approval service for task approval state in MVP.

Current storage uses JSONL for audit and SQLite for queryable task status.
The service never executes real RPA actions; it only records approval state.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import HTTPException

from src.repositories.sqlite_repository import (
    get_task_status_map,
    insert_approval_record,
    list_approval_records as list_sqlite_approval_records,
    upsert_task_status,
)
from src.services.log_service import create_execution_log, create_workflow_run, finish_workflow_run
from src.workflow.mock_workflow import build_mock_workflow_result

ROOT_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT_DIR / "logs"
APPROVAL_LOG_PATH = LOG_DIR / "approval_records.jsonl"

TASK_STATUS: Dict[str, Dict[str, Any]] = {}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False) + "\n")


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """Return one current approval action by task_id."""
    result = build_mock_workflow_result(write_outputs=False, record_logs=False)
    tasks = result.get("approval_required_tasks") or result.get("rpa_tasks", [])
    return next((item for item in tasks if item.get("task_id") == task_id), None)


def update_task_status(task_id: str, status: str, operator: str = "demo_user") -> Dict[str, Any]:
    workflow_run = create_workflow_run(
        workflow_type="task_approval",
        input_snapshot={"task_id": task_id, "target_status": status, "operator": operator},
    )
    workflow_run_id = workflow_run["workflow_run_id"]

    try:
        task = get_task(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

        if status not in {"approved", "rejected"}:
            raise HTTPException(status_code=400, detail="Invalid task status")

        updated = {
            **task,
            "approval_id": f"APPROVAL_{uuid4().hex[:10]}",
            "workflow_run_id": workflow_run_id,
            "approval_status": status,
            "status": status,
            "operator": operator,
            "updated_at": now_iso(),
            "execution_note": "MVP only records approval state; it does not execute real RPA actions.",
        }
        TASK_STATUS[task_id] = updated
        append_jsonl(APPROVAL_LOG_PATH, updated)
        insert_approval_record(updated)
        upsert_task_status(updated)
        create_execution_log(
            workflow_run_id=workflow_run_id,
            node_name="task_approval_record",
            status="success",
            input_snapshot={"task_id": task_id, "approval_status": status},
            output_snapshot={"task_id": task_id, "approval_status": status},
        )
        finish_workflow_run(
            workflow_run_id=workflow_run_id,
            workflow_type="task_approval",
            status="success",
            output_snapshot={"task_id": task_id, "approval_status": status},
        )
        return updated
    except Exception as exc:
        create_execution_log(
            workflow_run_id=workflow_run_id,
            node_name="task_approval_error",
            status="failed",
            error_message=str(exc),
        )
        finish_workflow_run(
            workflow_run_id=workflow_run_id,
            workflow_type="task_approval",
            status="failed",
            error_message=str(exc),
        )
        raise


def get_task_status_overrides() -> Dict[str, Dict[str, Any]]:
    persisted = get_task_status_map()
    return {**persisted, **TASK_STATUS}


def list_approval_records(limit: int = 50) -> list[Dict[str, Any]]:
    records = list_sqlite_approval_records(limit=limit)
    if records:
        return records
    if not APPROVAL_LOG_PATH.exists():
        return []
    lines = APPROVAL_LOG_PATH.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()][-limit:][::-1]
