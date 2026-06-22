"""Report task sync routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends

from src.core.context import UserContext, get_current_context
from src.services import module_task_service
from src.services.report_task_repository_sync_service import REPORT_TASK_SYNC_VERSION
from src.services.task_state_machine_service import mirror_all
from src.repositories.task_repository import TaskRepository

router = APIRouter(prefix="/api/data/report-tasks", tags=["report-task-sync"])


@router.post("/sync-current")
def sync_current_report_tasks(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Persist current report-created runtime tasks into TaskRepository."""

    repo = TaskRepository(ctx)
    synced_ids: list[str] = []
    for task in module_task_service.TASKS:
        if task.get("sourceRoute") == "data-check" or task.get("sourceModule") == "报表预警中心":
            repo.upsert(task)
            if task.get("id"):
                synced_ids.append(str(task.get("id")))
    mirror = mirror_all(module_task_service.TASKS, module_task_service.TASK_EVENTS, module_task_service.LOGS)
    return {
        "version": REPORT_TASK_SYNC_VERSION,
        "mode": "current_report_task_repository_sync",
        "syncedTaskIds": synced_ids,
        "syncedTaskCount": len(synced_ids),
        "repository": repo.summary(),
        "mirror": mirror,
    }
