"""Async SQLAlchemy repository transition layer.

These repositories are production targets. Current Demo routes still use SQLite runtime
repositories until DB_REPOSITORY_MODE is explicitly switched in later versions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.context import UserContext
from src.db.models import AuditLog, DecisionTask, ImportJob, WorkerJob

REPOSITORY_LAYER_VERSION = "5.3.1"


@dataclass(frozen=True)
class RepositoryScope:
    tenant_id: str
    org_id: str
    user_id: str
    store_ids: tuple[str, ...]
    role_id: str

    @classmethod
    def from_context(cls, ctx: UserContext) -> "RepositoryScope":
        return cls(
            tenant_id=ctx.tenant_id,
            org_id=ctx.org_id,
            user_id=ctx.user_id,
            store_ids=tuple(ctx.store_ids or []),
            role_id=ctx.role_id,
        )


def apply_scope(statement: Select[Any], model: Any, scope: RepositoryScope) -> Select[Any]:
    return statement.where(model.tenant_id == scope.tenant_id, model.org_id == scope.org_id, model.deleted_at.is_(None))


def task_to_dict(task: DecisionTask) -> dict[str, Any]:
    return {
        "taskId": task.task_id,
        "tenantId": task.tenant_id,
        "orgId": task.org_id,
        "traceId": task.trace_id,
        "sourceModule": task.source_module,
        "sourceEntityId": task.source_entity_id,
        "title": task.title,
        "status": task.status,
        "priority": task.priority,
        "assignedTo": task.assigned_to,
        "dueAt": task.due_at,
        "payload": task.payload or {},
        "createdAt": task.created_at.isoformat() if task.created_at else None,
        "updatedAt": task.updated_at.isoformat() if task.updated_at else None,
    }


def import_job_to_dict(job: ImportJob) -> dict[str, Any]:
    return {
        "importJobId": job.import_job_id,
        "tenantId": job.tenant_id,
        "orgId": job.org_id,
        "traceId": job.trace_id,
        "datasetName": job.dataset_name,
        "sourceType": job.source_type,
        "status": job.status,
        "rowCount": job.row_count,
        "alertCount": job.alert_count,
        "taskCount": job.task_count,
        "dataVersion": job.data_version,
        "inputSnapshot": job.input_snapshot or {},
        "outputSnapshot": job.output_snapshot or {},
        "errorMessage": job.error_message,
        "createdAt": job.created_at.isoformat() if job.created_at else None,
        "updatedAt": job.updated_at.isoformat() if job.updated_at else None,
    }


def worker_job_to_dict(job: WorkerJob) -> dict[str, Any]:
    return {
        "workerJobId": job.worker_job_id,
        "tenantId": job.tenant_id,
        "orgId": job.org_id,
        "traceId": job.trace_id,
        "queueName": job.queue_name,
        "jobType": job.job_type,
        "status": job.status,
        "priority": job.priority,
        "attemptCount": job.attempt_count,
        "maxAttempts": job.max_attempts,
        "idempotencyKey": job.idempotency_key,
        "correlationId": job.correlation_id,
        "payload": job.payload or {},
        "result": job.result or {},
        "errorMessage": job.error_message,
        "createdAt": job.created_at.isoformat() if job.created_at else None,
        "updatedAt": job.updated_at.isoformat() if job.updated_at else None,
    }


class ProductionTaskRepository:
    def __init__(self, session: AsyncSession, ctx: UserContext):
        self.session = session
        self.scope = RepositoryScope.from_context(ctx)

    async def list_visible(self, limit: int = 100) -> list[dict[str, Any]]:
        statement = apply_scope(select(DecisionTask), DecisionTask, self.scope).order_by(DecisionTask.updated_at.desc()).limit(limit)
        rows = (await self.session.scalars(statement)).all()
        return [task_to_dict(row) for row in rows]

    async def get(self, task_id: str) -> dict[str, Any] | None:
        statement = apply_scope(select(DecisionTask).where(DecisionTask.task_id == task_id), DecisionTask, self.scope)
        row = (await self.session.scalars(statement)).first()
        return task_to_dict(row) if row else None

    async def upsert(self, payload: dict[str, Any]) -> dict[str, Any]:
        task_id = str(payload.get("taskId") or payload.get("id"))
        existing = await self.session.get(DecisionTask, task_id)
        data = {
            "tenant_id": self.scope.tenant_id,
            "org_id": self.scope.org_id,
            "trace_id": payload.get("traceId") or payload.get("trace_id"),
            "source_module": payload.get("sourceModule") or payload.get("source_module"),
            "source_entity_id": payload.get("sourceEntityId") or payload.get("source_entity_id"),
            "title": payload.get("title") or "未命名任务",
            "status": payload.get("status") or "processing",
            "priority": payload.get("priority"),
            "assigned_to": payload.get("assignedTo") or payload.get("assigned_to"),
            "due_at": payload.get("dueAt") or payload.get("due_at"),
            "payload": payload,
            "updated_by": self.scope.user_id,
        }
        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
            task = existing
        else:
            task = DecisionTask(task_id=task_id, created_by=self.scope.user_id, **data)
            self.session.add(task)
        await self.session.flush()
        return task_to_dict(task)

    async def soft_delete_visible(self, reason: str = "repository_soft_delete") -> int:
        result = await self.session.execute(
            update(DecisionTask)
            .where(DecisionTask.tenant_id == self.scope.tenant_id, DecisionTask.org_id == self.scope.org_id, DecisionTask.deleted_at.is_(None))
            .values(deleted_at=func.now(), delete_reason=reason, deleted_by=self.scope.user_id, updated_by=self.scope.user_id)
        )
        return int(result.rowcount or 0)


class ProductionImportJobRepository:
    def __init__(self, session: AsyncSession, ctx: UserContext):
        self.session = session
        self.scope = RepositoryScope.from_context(ctx)

    async def list_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        statement = apply_scope(select(ImportJob), ImportJob, self.scope).order_by(ImportJob.created_at.desc()).limit(limit)
        rows = (await self.session.scalars(statement)).all()
        return [import_job_to_dict(row) for row in rows]

    async def get(self, import_job_id: str) -> dict[str, Any] | None:
        statement = apply_scope(select(ImportJob).where(ImportJob.import_job_id == import_job_id), ImportJob, self.scope)
        row = (await self.session.scalars(statement)).first()
        return import_job_to_dict(row) if row else None


class ProductionWorkerJobRepository:
    def __init__(self, session: AsyncSession, ctx: UserContext):
        self.session = session
        self.scope = RepositoryScope.from_context(ctx)

    async def list_jobs(self, queue_name: str | None = None, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        statement = apply_scope(select(WorkerJob), WorkerJob, self.scope)
        if queue_name:
            statement = statement.where(WorkerJob.queue_name == queue_name)
        if status:
            statement = statement.where(WorkerJob.status == status)
        rows = (await self.session.scalars(statement.order_by(WorkerJob.created_at.desc()).limit(limit))).all()
        return [worker_job_to_dict(row) for row in rows]


class ProductionAuditRepository:
    def __init__(self, session: AsyncSession, ctx: UserContext):
        self.session = session
        self.scope = RepositoryScope.from_context(ctx)

    async def trace_timeline(self, trace_id: str, limit: int = 100) -> list[dict[str, Any]]:
        statement = apply_scope(select(AuditLog).where(AuditLog.trace_id == trace_id), AuditLog, self.scope).order_by(AuditLog.created_at.asc()).limit(limit)
        rows = (await self.session.scalars(statement)).all()
        return [
            {
                "auditId": row.audit_id,
                "traceId": row.trace_id,
                "eventType": row.event_type,
                "resourceType": row.resource_type,
                "resourceId": row.resource_id,
                "action": row.action,
                "status": row.status,
                "payload": row.payload or {},
                "createdAt": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]


def production_repository_summary() -> dict[str, Any]:
    return {
        "version": REPOSITORY_LAYER_VERSION,
        "repositories": ["ProductionTaskRepository", "ProductionImportJobRepository", "ProductionWorkerJobRepository", "ProductionAuditRepository"],
        "scopeRule": "Every query applies tenant_id, org_id, and deleted_at IS NULL through apply_scope().",
        "writeRule": "This layer is ready for gradual migration; current Demo routes still use SQLite fallback unless explicitly switched.",
    }
