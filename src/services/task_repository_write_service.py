"""TaskRepository write-path transition service.

This service moves task creation and transitions toward database-backed writes
without breaking the existing demo runtime. The current in-memory service still
normalizes UI-facing task objects, while this layer immediately mirrors writes to
TaskRepository and keeps the repository summary observable.
"""

from __future__ import annotations

from typing import Any, Dict

from src.core.context import UserContext
from src.repositories.task_repository import TaskRepository
from src.services import module_task_service
from src.services.task_state_machine_service import ACTION_TARGET_STATUS, assert_transition_allowed, mirror_all

TASK_WRITE_VERSION = "5.1.3"


def _repository_response(ctx: UserContext, task: Dict[str, Any] | None, *, action: str, message: str) -> Dict[str, Any]:
    repo = TaskRepository(ctx)
    return {
        "version": TASK_WRITE_VERSION,
        "action": action,
        "message": message,
        "task": task,
        "repository": repo.summary(),
        "source": {
            "inMemoryTasks": len(module_task_service.TASKS),
            "inMemoryEvents": len(module_task_service.TASK_EVENTS),
            "inMemoryLogs": len(module_task_service.LOGS),
        },
        "nextStep": "Route module task APIs to this write service, then retire direct in-memory writes.",
    }


def create_task_with_repository(payload: Dict[str, Any], ctx: UserContext) -> Dict[str, Any]:
    """Create/merge a task through current runtime and persist the result."""

    task_payload = dict(payload)
    task_payload.setdefault("tenantId", ctx.tenant_id)
    task_payload.setdefault("orgId", ctx.org_id)
    task = module_task_service.create_task(task_payload)
    repo = TaskRepository(ctx)
    repo.upsert(task)
    mirror_all(module_task_service.TASKS, module_task_service.TASK_EVENTS, module_task_service.LOGS)
    return _repository_response(ctx, task, action="create_task", message="任务已通过 TaskRepository 写路径过渡层创建并持久化。")


def transition_task_with_repository(task_id: str, action: str, payload: Dict[str, Any] | None, ctx: UserContext) -> Dict[str, Any]:
    """Transition a task with state validation and repository persistence."""

    payload = payload or {}
    existing = module_task_service.find_task(task_id) or TaskRepository(ctx).get(task_id)
    if not existing:
        return _repository_response(ctx, None, action=action, message="任务不存在或当前账号无权访问。")
    from_status = existing.get("status")
    target_status = ACTION_TARGET_STATUS.get(action)
    assert_transition_allowed(from_status, target_status, action=action)
    task = module_task_service.transition_task(task_id, action, actor_user_id=payload.get("actorUserId") or ctx.user_id, payload=payload)
    if not task:
        return _repository_response(ctx, None, action=action, message="任务流转失败。")
    repo = TaskRepository(ctx)
    repo.upsert(task)
    mirror_all(module_task_service.TASKS, module_task_service.TASK_EVENTS, module_task_service.LOGS)
    return _repository_response(ctx, task, action=action, message="任务状态已通过 TaskRepository 写路径过渡层流转并持久化。")


def reset_tasks_with_repository(ctx: UserContext, *, reason: str = "demo reset") -> Dict[str, Any]:
    """Reset runtime tasks and soft-delete visible repository tasks."""

    repo = TaskRepository(ctx)
    deleted = repo.soft_delete_all_visible(deleted_by=ctx.user_id, reason=reason)
    module_task_service.reset_tasks(ctx.user_id)
    return {
        "version": TASK_WRITE_VERSION,
        "action": "reset_tasks",
        "message": "当前可见任务已软删除，Demo 内存任务池已清空。",
        "softDeletedTasks": deleted,
        "repository": repo.summary(),
        "source": {
            "inMemoryTasks": len(module_task_service.TASKS),
            "inMemoryEvents": len(module_task_service.TASK_EVENTS),
            "inMemoryLogs": len(module_task_service.LOGS),
        },
    }
