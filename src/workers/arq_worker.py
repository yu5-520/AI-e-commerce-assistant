"""ARQ worker entrypoint.

Run with:
    arq src.workers.arq_worker.WorkerSettings

This file is intentionally light: V5.2.2 establishes the Redis / ARQ contract
while SQLite worker_jobs remains the safe fallback for Demo deployments.
"""

from __future__ import annotations

from typing import Any, Dict

from arq.connections import RedisSettings

from src.core.context import UserContext
from src.services.worker_runtime_config_service import worker_runtime_config, worker_runtime_summary
from src.workers.task_registry import WORKER_TASK_REGISTRY, worker_task_registry_summary


async def arq_dispatch(ctx: Any, task_name: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Dispatch one registered task through the stable worker registry."""

    payload = payload or {}
    user_context = UserContext(
        tenant_id=payload.get("tenantId") or payload.get("tenant_id") or "tenant_demo",
        org_id=payload.get("orgId") or payload.get("org_id") or "org_demo",
        user_id=payload.get("userId") or payload.get("user_id") or "U001",
        role_id=payload.get("roleId") or payload.get("role_id") or "owner",
        role_name=payload.get("roleName") or payload.get("role_name") or "老板",
        permissions=payload.get("permissions") or [],
        store_group_ids=payload.get("storeGroupIds") or payload.get("store_group_ids") or [],
        store_ids=payload.get("storeIds") or payload.get("store_ids") or [],
        visible_modules=payload.get("visibleModules") or payload.get("visible_modules") or [],
        demo_mode=True,
    )
    handler = WORKER_TASK_REGISTRY.get(task_name)
    if not handler:
        return {"ok": False, "taskName": task_name, "error": "worker task not registered", "registry": worker_task_registry_summary()}
    result = handler(user_context, payload)
    if hasattr(result, "__await__"):
        result = await result  # type: ignore[assignment]
    return {"ok": True, "taskName": task_name, "result": result}


async def worker_health(ctx: Any) -> Dict[str, Any]:
    """Worker health check task."""

    return {"ok": True, "runtime": worker_runtime_summary(), "registry": worker_task_registry_summary()}


_config = worker_runtime_config()


class WorkerSettings:
    functions = [arq_dispatch, worker_health]
    redis_settings = RedisSettings.from_dsn(_config.redis_url)
    max_jobs = _config.max_jobs
    job_timeout = _config.job_timeout_seconds
    keep_result = _config.keep_result_seconds
