"""Production repositories for ProjectionJob, DataVersion, and AlertEvent."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.context import UserContext
from src.db.models import AlertEvent, DataVersion, ProjectionJob
from src.db.repositories import RepositoryScope, apply_scope

PROJECTION_REPOSITORY_VERSION = "5.3.5"


def projection_job_to_dict(row: ProjectionJob) -> dict[str, Any]:
    return {"projectionJobId": row.projection_job_id, "importJobId": row.import_job_id, "tenantId": row.tenant_id, "orgId": row.org_id, "traceId": row.trace_id, "projectionType": row.projection_type, "status": row.status, "inputSnapshot": row.input_snapshot or {}, "outputSnapshot": row.output_snapshot or {}, "errorMessage": row.error_message, "createdAt": row.created_at.isoformat() if row.created_at else None, "updatedAt": row.updated_at.isoformat() if row.updated_at else None}


def data_version_to_dict(row: DataVersion) -> dict[str, Any]:
    return {"dataVersion": row.data_version, "tenantId": row.tenant_id, "orgId": row.org_id, "traceId": row.trace_id, "importJobId": row.import_job_id, "datasetName": row.dataset_name, "sourceType": row.source_type, "status": row.status, "rowCount": row.row_count, "checksum": row.checksum, "payload": row.payload or {}, "createdAt": row.created_at.isoformat() if row.created_at else None}


def alert_event_to_dict(row: AlertEvent) -> dict[str, Any]:
    return {"alertId": row.alert_id, "tenantId": row.tenant_id, "orgId": row.org_id, "traceId": row.trace_id, "dataVersion": row.data_version, "sourceModule": row.source_module, "sourceEntityId": row.source_entity_id, "alertType": row.alert_type, "severity": row.severity, "status": row.status, "title": row.title, "payload": row.payload or {}, "createdAt": row.created_at.isoformat() if row.created_at else None}


class ProductionProjectionJobRepository:
    def __init__(self, session: AsyncSession, ctx: UserContext):
        self.session = session
        self.scope = RepositoryScope.from_context(ctx)

    async def upsert(self, payload: dict[str, Any]) -> dict[str, Any]:
        projection_job_id = str(payload.get("projectionJobId") or payload.get("projection_job_id"))
        existing = await self.session.get(ProjectionJob, projection_job_id)
        data = {"tenant_id": self.scope.tenant_id, "org_id": self.scope.org_id, "trace_id": payload.get("traceId") or payload.get("trace_id"), "import_job_id": payload.get("importJobId") or payload.get("import_job_id"), "projection_type": payload.get("projectionType") or payload.get("projection_type") or "module_projection_refresh", "status": payload.get("status") or "completed", "input_snapshot": payload.get("inputSnapshot") or payload.get("input_snapshot") or {}, "output_snapshot": payload.get("outputSnapshot") or payload.get("output_snapshot") or {}, "error_message": payload.get("errorMessage") or payload.get("error_message")}
        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
            row = existing
        else:
            row = ProjectionJob(projection_job_id=projection_job_id, **data)
            self.session.add(row)
        await self.session.flush()
        return projection_job_to_dict(row)

    async def list_by_import(self, import_job_id: str, limit: int = 100) -> list[dict[str, Any]]:
        statement = apply_scope(select(ProjectionJob).where(ProjectionJob.import_job_id == import_job_id), ProjectionJob, self.scope).order_by(ProjectionJob.created_at.asc()).limit(limit)
        rows = (await self.session.scalars(statement)).all()
        return [projection_job_to_dict(row) for row in rows]


class ProductionDataVersionRepository:
    def __init__(self, session: AsyncSession, ctx: UserContext):
        self.session = session
        self.scope = RepositoryScope.from_context(ctx)

    async def upsert(self, payload: dict[str, Any]) -> dict[str, Any]:
        data_version = str(payload.get("dataVersion") or payload.get("data_version"))
        existing = await self.session.get(DataVersion, data_version)
        data = {"tenant_id": self.scope.tenant_id, "org_id": self.scope.org_id, "trace_id": payload.get("traceId") or payload.get("trace_id"), "import_job_id": payload.get("importJobId") or payload.get("import_job_id"), "dataset_name": payload.get("datasetName") or payload.get("dataset_name"), "source_type": payload.get("sourceType") or payload.get("source_type"), "status": payload.get("status") or "active", "row_count": int(payload.get("rowCount") or payload.get("row_count") or 0), "checksum": payload.get("checksum"), "payload": payload.get("payload") or {}}
        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
            row = existing
        else:
            row = DataVersion(data_version=data_version, created_by=self.scope.user_id, **data)
            self.session.add(row)
        await self.session.flush()
        return data_version_to_dict(row)


class ProductionAlertEventRepository:
    def __init__(self, session: AsyncSession, ctx: UserContext):
        self.session = session
        self.scope = RepositoryScope.from_context(ctx)

    async def upsert(self, payload: dict[str, Any]) -> dict[str, Any]:
        alert_id = str(payload.get("alertId") or payload.get("alert_id"))
        existing = await self.session.get(AlertEvent, alert_id)
        data = {"tenant_id": self.scope.tenant_id, "org_id": self.scope.org_id, "trace_id": payload.get("traceId") or payload.get("trace_id"), "data_version": payload.get("dataVersion") or payload.get("data_version"), "source_module": payload.get("sourceModule") or payload.get("source_module"), "source_entity_id": payload.get("sourceEntityId") or payload.get("source_entity_id"), "alert_type": payload.get("alertType") or payload.get("alert_type") or "runtime_alert", "severity": payload.get("severity") or "medium", "status": payload.get("status") or "open", "title": payload.get("title") or "未命名预警", "payload": payload.get("payload") or {}}
        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
            row = existing
        else:
            row = AlertEvent(alert_id=alert_id, **data)
            self.session.add(row)
        await self.session.flush()
        return alert_event_to_dict(row)


def projection_repository_summary() -> dict[str, Any]:
    return {"version": PROJECTION_REPOSITORY_VERSION, "repositories": ["ProductionProjectionJobRepository", "ProductionDataVersionRepository", "ProductionAlertEventRepository"], "rule": "ProjectionJob can mirror from SQLite Demo; DataVersion and AlertEvent production models are ready for the next write-path migration."}
