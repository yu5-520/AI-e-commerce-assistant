"""Worker queue scaffold routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from src.core.context import UserContext, get_current_context
from src.services.worker_queue_service import (
    claim_next_worker_job,
    complete_worker_job,
    enqueue_worker_job,
    fail_worker_job,
    list_worker_jobs,
    retry_worker_job,
    worker_queue_summary,
)
from src.services.worker_runtime_config_service import worker_runtime_summary
from src.workers.task_registry import worker_task_registry_summary

router = APIRouter(prefix="/api/worker/jobs", tags=["worker-jobs"])


@router.get("/runtime")
def worker_runtime() -> Dict[str, Any]:
    """Return Redis / ARQ runtime config and registered worker tasks."""

    return {"runtime": worker_runtime_summary(), "registry": worker_task_registry_summary()}


@router.get("/summary")
def worker_summary(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Return queue status counts for the current tenant."""

    return worker_queue_summary(ctx)


@router.get("")
def worker_jobs(
    queue_name: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    ctx: UserContext = Depends(get_current_context),
) -> Dict[str, Any]:
    """List worker jobs scoped by tenant."""

    return list_worker_jobs(ctx, queue_name=queue_name, status=status, limit=limit)


@router.post("/enqueue")
def enqueue_job(body: Dict[str, Any] = Body(default_factory=dict), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Enqueue one worker job into the SQLite scaffold queue."""

    try:
        return enqueue_worker_job(ctx, body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/claim-next")
def claim_next_job(
    body: Dict[str, Any] = Body(default_factory=dict),
    ctx: UserContext = Depends(get_current_context),
) -> Dict[str, Any]:
    """Claim the next queued job for a demo worker."""

    result = claim_next_worker_job(
        ctx,
        queue_name=body.get("queueName") or body.get("queue_name") or "default",
        worker_id=body.get("workerId") or body.get("worker_id") or "worker-demo",
    )
    if not result:
        return {"message": "no queued job", "queueName": body.get("queueName") or body.get("queue_name") or "default", "job": None}
    return result


@router.post("/{worker_job_id}/complete")
def complete_job(worker_job_id: str, body: Dict[str, Any] = Body(default_factory=dict), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Mark one worker job completed."""

    result = complete_worker_job(ctx, worker_job_id, result=body.get("result") or body)
    if not result:
        raise HTTPException(status_code=404, detail="worker job not found")
    return result


@router.post("/{worker_job_id}/fail")
def fail_job(worker_job_id: str, body: Dict[str, Any] = Body(default_factory=dict), ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Mark one worker job failed or schedule retry."""

    result = fail_worker_job(
        ctx,
        worker_job_id,
        error_message=body.get("errorMessage") or body.get("error_message") or "worker failed",
        retry=body.get("retry", True) is not False,
    )
    if not result:
        raise HTTPException(status_code=404, detail="worker job not found")
    return result


@router.post("/{worker_job_id}/retry")
def retry_job(worker_job_id: str, ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    """Move a failed / retry_scheduled job back to queued."""

    result = retry_worker_job(ctx, worker_job_id)
    if not result:
        raise HTTPException(status_code=404, detail="worker job not found or not retryable")
    return result
