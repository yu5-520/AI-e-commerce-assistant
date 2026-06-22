"""ImportJob worker queue bridge."""

from __future__ import annotations

from typing import Any, Dict

from src.core.context import UserContext
from src.services.arq_dispatch_service import dispatch_arq_or_fallback
from src.services.import_job_service import run_import_job
from src.services.report_alert_service import import_report_dataset, run_v3_mock_imports
from src.services.report_schema_service import confirm_report_import
from src.services.trace_audit_service import resolve_trace_id
from src.services.worker_queue_service import claim_next_worker_job, complete_worker_job, enqueue_worker_job, fail_worker_job

IMPORT_JOB_WORKER_VERSION = "5.2.5"
IMPORT_QUEUE_NAME = "import"


def enqueue_import_worker_job(ctx: UserContext, *, dataset_name: str, source_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    trace_id = resolve_trace_id(payload, "IMPORTTRACE")
    worker_payload = {
        "queueName": IMPORT_QUEUE_NAME,
        "jobType": "import_report",
        "priority": payload.get("priority") or 30,
        "maxAttempts": payload.get("maxAttempts") or payload.get("max_attempts") or 3,
        "idempotencyKey": payload.get("idempotencyKey") or payload.get("idempotency_key"),
        "correlationId": payload.get("correlationId") or payload.get("correlation_id") or trace_id,
        "payload": {"version": IMPORT_JOB_WORKER_VERSION, "traceId": trace_id, "datasetName": dataset_name, "sourceType": source_type, "body": {**payload, "traceId": trace_id}},
    }
    queued = enqueue_worker_job(ctx, worker_payload)
    worker_job = queued.get("job") or {}
    trace_id = worker_job.get("traceId") or trace_id
    dispatch = dispatch_arq_or_fallback(
        ctx,
        "import_report",
        {"traceId": trace_id, "workerJobId": worker_job.get("workerJobId"), "workerId": "arq-import-worker", "queueName": IMPORT_QUEUE_NAME, "sourceType": source_type, "datasetName": dataset_name},
    )
    return {"version": IMPORT_JOB_WORKER_VERSION, "traceId": trace_id, "mode": "import_job_enqueue", "importQueued": True, "workerJob": worker_job, "created": queued.get("created"), "arqDispatch": dispatch, "rule": "enqueue=true writes worker_jobs first; Redis / ARQ dispatch is optional and falls back to SQLite."}


def _run_import_payload(ctx: UserContext, payload: Dict[str, Any]) -> Dict[str, Any]:
    trace_id = resolve_trace_id(payload, "IMPORTTRACE")
    dataset_name = payload.get("datasetName") or payload.get("dataset_name") or "mock-alerts"
    source_type = payload.get("sourceType") or payload.get("source_type") or "confirm_report_import"
    body = {**(payload.get("body") or {}), "traceId": trace_id}
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
        return run_import_job(ctx, dataset_name="mock-alerts", source_type=source_type, payload=body, runner=lambda: run_v3_mock_imports(dataset_names=dataset_names))
    raise ValueError(f"unsupported import worker sourceType: {source_type}")


def execute_next_import_worker_job(ctx: UserContext, *, worker_id: str = "import-worker-demo") -> Dict[str, Any]:
    claimed = claim_next_worker_job(ctx, queue_name=IMPORT_QUEUE_NAME, worker_id=worker_id)
    if not claimed or not claimed.get("job"):
        return {"version": IMPORT_JOB_WORKER_VERSION, "mode": "import_worker_execute_next", "job": None, "message": "no queued import job"}
    job = claimed["job"]
    try:
        result = _run_import_payload(ctx, job.get("payload") or {})
        completed = complete_worker_job(ctx, job["workerJobId"], result=result)
        return {"version": IMPORT_JOB_WORKER_VERSION, "traceId": job.get("traceId"), "mode": "import_worker_execute_next", "workerJob": completed.get("job") if completed else job, "importResult": result}
    except Exception as exc:  # noqa: BLE001
        failed = fail_worker_job(ctx, job["workerJobId"], error_message=str(exc), retry=True)
        return {"version": IMPORT_JOB_WORKER_VERSION, "traceId": job.get("traceId"), "mode": "import_worker_execute_next", "workerJob": failed.get("job") if failed else job, "error": str(exc)}
