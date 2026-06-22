"""Task persistence mirror routes for the P0 SaaS upgrade."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends

from src.core.context import UserContext, get_current_context
from src.repositories.task_repository import TaskRepository
from src.services import module_task_service
from src.services.task_repository_write_service import create_task_with_repository, reset_tasks_with_repository, transition_task_with_repository
from src.services.task_state_machine_service import mirror_all, task_persistence_summary

router = APIRouter(prefix="/api/architecture/tasks", tags=["architecture"])


@router.get("/persistence")
def task_persistence(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Return the current SQLite task persistence mirror and scoped repository status."""

    repo = TaskRepository(ctx)
    return {
        "mirror": task_persistence_summary(),
        "repository": repo.summary(),
    }


@router.get("/repository")
def repository_tasks(
    active_only: bool = False,
    limit: int = 100,
    ctx: UserContext = Depends(get_current_context),
) -> Dict[str, Any]:
    """Read tasks from TaskRepository with tenant / store / deleted_at filtering."""

    repo = TaskRepository(ctx)
    tasks = repo.list(active_only=active_only, limit=limit)
    return {
        "source": "TaskRepository(SQLite mirror)",
        "count": len(tasks),
        "tasks": tasks,
        "summary": repo.summary(),
    }


@router.post("/repository/create")
def repository_create_task(payload: Dict[str, Any], ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Create/merge a task through the TaskRepository write-path transition layer."""

    return create_task_with_repository(payload, ctx)


@router.post("/repository/{task_id}/transition/{action}")
def repository_transition_task(
    task_id: str,
    action: str,
    payload: Dict[str, Any] | None = None,
    ctx: UserContext = Depends(get_current_context),
) -> Dict[str, Any]:
    """Transition a task through the TaskRepository write-path transition layer."""

    return transition_task_with_repository(task_id, action, payload or {}, ctx)


@router.post("/repository/reset")
def repository_reset_tasks(payload: Dict[str, Any] | None = None, ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Soft-delete visible repository tasks and clear the demo runtime task pool."""

    payload = payload or {}
    return reset_tasks_with_repository(ctx, reason=payload.get("reason") or "repository reset")


@router.post("/sync-runtime")
def sync_runtime_tasks(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Mirror current in-memory demo task runtime into SQLite P0 tables.

    This keeps the current UI safe while preparing the final TaskRepository
    replacement. It can be called after demo imports or task flow testing.
    """

    summary = mirror_all(
        module_task_service.TASKS,
        module_task_service.TASK_EVENTS,
        module_task_service.LOGS,
    )
    repo = TaskRepository(ctx)
    return {
        "message": "当前 Demo 任务运行态已同步到 SQLite P0 任务表。",
        "summary": summary,
        "repository": repo.summary(),
        "source": {
            "inMemoryTasks": len(module_task_service.TASKS),
            "inMemoryEvents": len(module_task_service.TASK_EVENTS),
            "inMemoryLogs": len(module_task_service.LOGS),
        },
        "nextStep": "验证无误后，将前端任务动作切换到 /api/architecture/tasks/repository/* 写路径。",
    }
