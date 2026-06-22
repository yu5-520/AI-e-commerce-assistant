"""Worker task registry.

The registry keeps worker task names stable while implementations can move from
SQLite demo execution to Redis / ARQ background processing.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from src.core.context import UserContext
from src.services.import_job_worker_service import execute_next_import_worker_job
from src.services.report_task_repository_sync_service import sync_report_tasks

WORKER_REGISTRY_VERSION = "5.2.2"
WorkerHandler = Callable[[UserContext, Dict[str, Any]], Dict[str, Any] | Awaitable[Dict[str, Any]]]


def run_import_worker(ctx: UserContext, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the next queued import job using the current demo worker bridge."""

    return execute_next_import_worker_job(ctx, worker_id=payload.get("workerId") or payload.get("worker_id") or "arq-import-worker")


def run_report_task_sync(ctx: UserContext, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Sync report-created runtime tasks into TaskRepository."""

    return sync_report_tasks(payload.get("result") or {}, ctx)


WORKER_TASK_REGISTRY: Dict[str, WorkerHandler] = {
    "import_report": run_import_worker,
    "task_repository_sync": run_report_task_sync,
}


def worker_task_registry_summary() -> Dict[str, Any]:
    return {
        "version": WORKER_REGISTRY_VERSION,
        "registeredTasks": sorted(WORKER_TASK_REGISTRY.keys()),
        "plannedTasks": ["projection_refresh", "alert_generation", "agent_analysis", "rag_memory_write"],
        "rule": "未注册任务仍保留在 SQLite worker_jobs 中，不由 ARQ 直接执行。",
    }
