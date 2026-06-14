"""Approval service for task approval state in MVP.

Current storage is in-memory plus JSONL append log. This keeps the API simple
while preserving traceability. Later it can be replaced by SQLite or PostgreSQL.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from fastapi import HTTPException

from src.services.log_service import create_execution_log, create_workflow_run, finish_workflow_run
from src.services.workflow_service import get_task

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
            "workflow_run_id": workflow_run_id,
            "approval_status": status,
            "status": status,
            "operator": operator,
            "updated_at": now_iso(),
            "execution_note": "MVP only records approval state; it does not execute real RPA actions.",
        }
        TASK_STATUS[task_id] = updated
        append_jsonl(APPROVAL_LOG_PATH, updated)
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
    return TASK_STATUS
