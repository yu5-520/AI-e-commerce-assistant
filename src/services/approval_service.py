"""Approval service for task approval state in MVP.

Current storage is in-memory plus JSONL append log. This keeps the API simple
while preserving a traceable approval record. Later it can be replaced by
SQLite or PostgreSQL.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from fastapi import HTTPException

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
    task = get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    if status not in {"approved", "rejected"}:
        raise HTTPException(status_code=400, detail="Invalid task status")

    updated = {
        **task,
        "approval_status": status,
        "status": status,
        "operator": operator,
        "updated_at": now_iso(),
        "execution_note": "MVP only records approval state; it does not execute real RPA actions.",
    }
    TASK_STATUS[task_id] = updated
    append_jsonl(APPROVAL_LOG_PATH, updated)
    return updated


def get_task_status_overrides() -> Dict[str, Dict[str, Any]]:
    return TASK_STATUS
