"""Worker task registry."""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from src.core.context import UserContext
from src.services.import_job_worker_service import execute_next_import_worker_job
from src.services.report_task_repository_sync_service import sync_report_tasks
from src.services.worker_task_handlers_service import run_agent_analysis, run_alert_generation, run_projection_refresh, run_rag_memory_write

WORKER_REGISTRY_VERSION = "5.2.4"
WorkerHandler = Callable[[UserContext, Dict[str, Any]], Dict[str, Any] | Awaitable[Dict[str, Any]]]


def run_import_worker(ctx: UserContext, payload: Dict[str, Any]) -> Dict[str, Any]:
    return execute_next_import_worker_job(ctx, worker_id=payload.get("workerId") or payload.get("worker_id") or "arq-import-worker")


def run_report_task_sync(ctx: UserContext, payload: Dict[str, Any]) -> Dict[str, Any]:
    return sync_report_tasks(payload.get("result") or {}, ctx)


WORKER_TASK_REGISTRY: Dict[str, WorkerHandler] = {
    "import_report": run_import_worker,
    "task_repository_sync": run_report_task_sync,
    "projection_refresh": run_projection_refresh,
    "alert_generation": run_alert_generation,
    "agent_analysis": run_agent_analysis,
    "rag_memory_write": run_rag_memory_write,
}


def worker_task_registry_summary() -> Dict[str, Any]:
    return {
        "version": WORKER_REGISTRY_VERSION,
        "registeredTasks": sorted(WORKER_TASK_REGISTRY.keys()),
        "plannedTasks": [],
        "rule": "Worker 任务已注册为可执行 handler；经营动作仍需人工确认或走 TaskRepository 写路径。",
    }
