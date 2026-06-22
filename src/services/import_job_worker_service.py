"""ImportJob worker queue bridge.

V5.2.1 keeps the existing synchronous ImportJob path, but adds an enqueue mode
and a demo executor that claims one queued import job and runs the same import
logic. Redis / ARQ can later replace the claim/execute implementation while
keeping this contract.
"""

from __future__ import annotations

from typing import Any, Dict

from src.core.context import UserContext
from src.services.import_job_service import run_import_job
from src.services.report_alert_service import import_report_dataset, run_v3_mock_imports
from src.services.report_schema_service import confirm_report_import
from src.services.worker_queue_service import claim_next_worker_job, complete_worker_job, enqueue_worker_job, fail_worker_job

IMPORT_JOB_WORKER_VERSION = "5.2.1"
IMPORT_QUEUE_NAME = "import"


def enqueue_import_worker_job(
    ctx: UserContext,
    *,
    dataset_name: str,
    source_type: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """Queue an import request instead of running it in the request thread."""

    worker_payload = {
        "queueName": IMPORT_QUEUE_NAME,
        "jobType": "import_report",
        "priority": payload.get("priority") or 30,
        "maxAttempts": payload.get("maxAttempts") or payload.get("max_attempts") or 3,
        "idempotencyKey": payload.get("idempotencyKey") or payload.get("idempotency_key"),
        "correlationId": payload.get("correlationId") or payload.get("correlation_id"),
        "payload": {
            "version": IMPORT_JOB_WORKER_VERSION,
            "datasetName": dataset_name,
            "sourceType": source_type,
            "body": payload,
        },
    }
    queued = enqueue_worker_job(ctx, worker_payload)
    return {
        "version": IMPORT_JOB_WORKER_VERSION,
        "mode": "import_job_enqueue",
        "importQueued": True,
        "workerJob": queued.get("job"),
        "created": queued.get("created"),
        "rule": "enqueue=true 时只入队，不在请求线程执行导入；由 /api/data/import-jobs/worker/execute-next 消费。",
    }


def _run_import_payload(ctx: UserContext, payload: Dict[str, Any]) -> Dict[str, Any]:
    dataset_name = payload.get("datasetName") or payload.get("dataset_name") or "mock-alerts"
    source_type = payload.get("sourceType") or payload.get("source_type") or "confirm_report_import"
    body = payload.get("body") or {}
    if source_type == "confirm_report_import":
        return run_import_job(
            ctx,
            dataset_name=str(dataset_name),
            source_type=source_type,
            payload=body,
            runner=lambda: confirm_report_import(
                str(dataset_name),
                rows=body.get("rows"),
                field_mapping=body.get("field_mapping") or body.get("fieldMapping"),
                auto_create_tasks=body.get("auto_create_tasks", body.get("autoCreateTasks", True)) is not False,
            ),
        )
    if source_type == "import_report_dataset":
        return run_import_job(
            ctx,
            dataset_name=str(dataset_name),
            source_type=source_type,
            payload=body,
            runner=lambda: import_report_dataset(
                str(dataset_name),
                rows=body.get("rows"),
                auto_create_tasks=body.get("auto_create_tasks", body.get("autoCreateTasks", True)) is not False,
            ),
        )
    if source_type == "run_v3_mock_imports":
        dataset_names = body.get("dataset_names") or body.get("datasetNames")
        return run_import_job(
            ctx,
            dataset_name="mock-alerts",
            source_type=source_type,
            payload=body,
            runner=lambda: run_v3_mock_imports(dataset_names=dataset_names),
        )
    raise ValueError(f"unsupported import worker sourceType: {source_type}")


def execute_next_import_worker_job(ctx: UserContext, *, worker_id: str = "import-worker-demo") -> Dict[str, Any]:
    """Claim and execute one queued import job in-process for demo validation."""

    claimed = claim_next_worker_job(ctx, queue_name=IMPORT_QUEUE_NAME, worker_id=worker_id)
    if not claimed or not claimed.get("job"):
        return {"version": IMPORT_JOB_WORKER_VERSION, "mode": "import_worker_execute_next", "job": None, "message": "no queued import job"}
    job = claimed["job"]
    try:
        result = _run_import_payload(ctx, job.get("payload") or {})
        completed = complete_worker_job(ctx, job["workerJobId"], result=result)
        return {
            "version": IMPORT_JOB_WORKER_VERSION,
            "mode": "import_worker_execute_next",
            "workerJob": completed.get("job") if completed else job,
            "importResult": result,
        }
    except Exception as exc:  # noqa: BLE001 - keep demo worker robust and observable.
        failed = fail_worker_job(ctx, job["workerJobId"], error_message=str(exc), retry=True)
        return {
            "version": IMPORT_JOB_WORKER_VERSION,
            "mode": "import_worker_execute_next",
            "workerJob": failed.get("job") if failed else job,
            "error": str(exc),
        }
