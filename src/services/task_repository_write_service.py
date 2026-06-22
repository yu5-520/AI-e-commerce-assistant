"""TaskRepository write-path transition service with trace audit."""

from __future__ import annotations

from typing import Any, Dict

from src.core.context import UserContext
from src.repositories.task_repository import TaskRepository
from src.services import module_task_service
from src.services.task_state_machine_service import ACTION_TARGET_STATUS, assert_transition_allowed, mirror_all
from src.services.trace_audit_service import resolve_trace_id, write_audit_log

TASK_WRITE_VERSION = "5.2.6"


def _task_id(task: Dict[str, Any] | None) -> str | None:
    if not task:
        return None
    return task.get("id") or task.get("taskId") or task.get("task_id")


def _repository_response(ctx: UserContext, task: Dict[str, Any] | None, *, action: str, message: str, trace_id: str | None = None) -> Dict[str, Any]:
    repo = TaskRepository(ctx)
    return {
        "version": TASK_WRITE_VERSION,
        "traceId": trace_id,
        "action": action,
        "message": message,
        "task": task,
        "repository": repo.summary(),
        "source": {
            "inMemoryTasks": len(module_task_service.TASKS),
            "inMemoryEvents": len(module_task_service.TASK_EVENTS),
            "inMemoryLogs": len(module_task_service.LOGS),
        },
        "nextStep": "Task / Evidence / RAG Memory are being linked into trace_id audit chain.",
    }


def create_task_with_repository(payload: Dict[str, Any], ctx: UserContext) -> Dict[str, Any]:
    """Create/merge a task through current runtime and persist the result."""

    trace_id = resolve_trace_id(payload, "TASKTRACE")
    task_payload = {**dict(payload), "traceId": trace_id}
    task_payload.setdefault("tenantId", ctx.tenant_id)
    task_payload.setdefault("orgId", ctx.org_id)
    task = module_task_service.create_task(task_payload)
    if isinstance(task, dict):
        task["traceId"] = task.get("traceId") or trace_id
    repo = TaskRepository(ctx)
    repo.upsert(task)
    mirror_all(module_task_service.TASKS, module_task_service.TASK_EVENTS, module_task_service.LOGS)
    write_audit_log(ctx, trace_id=trace_id, event_type="task.created", resource_type="task", resource_id=_task_id(task), action="create_task", status=(task or {}).get("status"), payload={"sourceModule": (task or {}).get("sourceModule"), "title": (task or {}).get("title")})
    return _repository_response(ctx, task, action="create_task", message="任务已通过 TaskRepository 写路径过渡层创建并写入 trace audit。", trace_id=trace_id)


def transition_task_with_repository(task_id: str, action: str, payload: Dict[str, Any] | None, ctx: UserContext) -> Dict[str, Any]:
    """Transition a task with state validation and repository persistence."""

    payload = payload or {}
    existing = module_task_service.find_task(task_id) or TaskRepository(ctx).get(task_id)
    trace_id = resolve_trace_id(payload or existing or {"taskId": task_id}, "TASKTRACE")
    if not existing:
        write_audit_log(ctx, trace_id=trace_id, event_type="task.transition_missing", resource_type="task", resource_id=task_id, action=action, status="not_found", payload={})
        return _repository_response(ctx, None, action=action, message="任务不存在或当前账号无权访问。", trace_id=trace_id)
    from_status = existing.get("status")
    target_status = ACTION_TARGET_STATUS.get(action)
    assert_transition_allowed(from_status, target_status, action=action)
    task = module_task_service.transition_task(task_id, action, actor_user_id=payload.get("actorUserId") or ctx.user_id, payload={**payload, "traceId": trace_id})
    if not task:
        write_audit_log(ctx, trace_id=trace_id, event_type="task.transition_failed", resource_type="task", resource_id=task_id, action=action, status="failed", payload={"fromStatus": from_status, "targetStatus": target_status})
        return _repository_response(ctx, None, action=action, message="任务流转失败。", trace_id=trace_id)
    task["traceId"] = task.get("traceId") or trace_id
    repo = TaskRepository(ctx)
    repo.upsert(task)
    mirror_all(module_task_service.TASKS, module_task_service.TASK_EVENTS, module_task_service.LOGS)
    write_audit_log(ctx, trace_id=trace_id, event_type="task.transitioned", resource_type="task", resource_id=task_id, action=action, status=task.get("status"), payload={"fromStatus": from_status, "targetStatus": target_status})
    return _repository_response(ctx, task, action=action, message="任务状态已通过 TaskRepository 写路径过渡层流转并写入 trace audit。", trace_id=trace_id)


def reset_tasks_with_repository(ctx: UserContext, *, reason: str = "demo reset") -> Dict[str, Any]:
    """Reset runtime tasks and soft-delete visible repository tasks."""

    trace_id = resolve_trace_id({"reason": reason}, "TASKRESET")
    repo = TaskRepository(ctx)
    deleted = repo.soft_delete_all_visible(deleted_by=ctx.user_id, reason=reason)
    module_task_service.reset_tasks(ctx.user_id)
    write_audit_log(ctx, trace_id=trace_id, event_type="task.reset", resource_type="task", resource_id="visible_tasks", action="reset_tasks", status="completed", payload={"reason": reason, "softDeletedTasks": deleted})
    return {
        "version": TASK_WRITE_VERSION,
        "traceId": trace_id,
        "action": "reset_tasks",
        "message": "当前可见任务已软删除，Demo 内存任务池已清空，并写入 trace audit。",
        "softDeletedTasks": deleted,
        "repository": repo.summary(),
        "source": {
            "inMemoryTasks": len(module_task_service.TASKS),
            "inMemoryEvents": len(module_task_service.TASK_EVENTS),
            "inMemoryLogs": len(module_task_service.LOGS),
        },
    }
