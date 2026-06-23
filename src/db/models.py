"""Production SQLAlchemy models for the SaaS P0 data model scaffold."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import ActorMixin, Base, SoftDeleteMixin, TenantScopedMixin, TimestampMixin, TraceAuditMixin

MODEL_VERSION = "5.3.5"


class Tenant(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "tenants"
    tenant_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)


class Organization(Base, TenantScopedMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "organizations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)


class User(Base, TenantScopedMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"
    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)


class Store(Base, TenantScopedMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "stores"
    store_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    store_name: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str | None] = mapped_column(String(64), nullable=True)
    operator_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)


class ImportJob(Base, TenantScopedMixin, TimestampMixin, SoftDeleteMixin, TraceAuditMixin, ActorMixin):
    __tablename__ = "import_jobs"
    import_job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    dataset_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    alert_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    task_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    data_version: Mapped[str | None] = mapped_column(String(96), nullable=True, index=True)
    input_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class ProjectionJob(Base, TenantScopedMixin, TimestampMixin, SoftDeleteMixin, TraceAuditMixin):
    __tablename__ = "projection_jobs"
    projection_job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    import_job_id: Mapped[str] = mapped_column(String(64), ForeignKey("import_jobs.import_job_id"), nullable=False, index=True)
    projection_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    input_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class DataVersion(Base, TenantScopedMixin, TimestampMixin, SoftDeleteMixin, TraceAuditMixin, ActorMixin):
    __tablename__ = "data_versions"
    data_version: Mapped[str] = mapped_column(String(96), primary_key=True)
    import_job_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("import_jobs.import_job_id"), nullable=True, index=True)
    dataset_name: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    source_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False, index=True)
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class AlertEvent(Base, TenantScopedMixin, TimestampMixin, SoftDeleteMixin, TraceAuditMixin):
    __tablename__ = "alert_events"
    alert_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    data_version: Mapped[str | None] = mapped_column(String(96), nullable=True, index=True)
    source_module: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    source_entity_id: Mapped[str | None] = mapped_column(String(96), nullable=True, index=True)
    alert_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(32), default="medium", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class DecisionTask(Base, TenantScopedMixin, TimestampMixin, SoftDeleteMixin, TraceAuditMixin, ActorMixin):
    __tablename__ = "decision_tasks"
    task_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_module: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    source_entity_id: Mapped[str | None] = mapped_column(String(96), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    priority: Mapped[str | None] = mapped_column(String(32), nullable=True)
    assigned_to: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    due_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class TaskEvent(Base, TenantScopedMixin, TimestampMixin, SoftDeleteMixin, TraceAuditMixin):
    __tablename__ = "task_events"
    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    task_id: Mapped[str] = mapped_column(String(64), ForeignKey("decision_tasks.task_id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    actor_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class TaskEvidence(Base, TenantScopedMixin, TimestampMixin, SoftDeleteMixin, TraceAuditMixin):
    __tablename__ = "task_evidence"
    evidence_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    task_id: Mapped[str] = mapped_column(String(64), ForeignKey("decision_tasks.task_id"), nullable=False, index=True)
    submitter_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class WorkerJob(Base, TenantScopedMixin, TimestampMixin, SoftDeleteMixin, TraceAuditMixin, ActorMixin):
    __tablename__ = "worker_jobs"
    __table_args__ = (UniqueConstraint("tenant_id", "idempotency_key", name="uq_worker_jobs_tenant_idempotency"),)
    worker_job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    queue_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    job_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class AuditLog(Base, TenantScopedMixin, TimestampMixin, SoftDeleteMixin, TraceAuditMixin):
    __tablename__ = "audit_logs"
    audit_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    actor_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_type: Mapped[str] = mapped_column(String(96), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(96), nullable=True)
    action: Mapped[str | None] = mapped_column(String(96), nullable=True)
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class TechLog(Base, TenantScopedMixin, TimestampMixin, SoftDeleteMixin, TraceAuditMixin):
    __tablename__ = "tech_logs"
    log_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    actor_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    level: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    logger: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_type: Mapped[str] = mapped_column(String(96), nullable=False, index=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class LLMGatewayEvent(Base, TenantScopedMixin, TimestampMixin, SoftDeleteMixin, TraceAuditMixin):
    __tablename__ = "llm_gateway_events"
    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    schema_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    cache_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    request_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)


def model_registry_summary() -> dict[str, object]:
    return {"version": MODEL_VERSION, "models": ["Tenant", "Organization", "User", "Store", "ImportJob", "ProjectionJob", "DataVersion", "AlertEvent", "DecisionTask", "TaskEvent", "TaskEvidence", "WorkerJob", "AuditLog", "TechLog", "LLMGatewayEvent"], "rule": "Models are production schema targets for Alembic; current Demo SQLite services remain unchanged until migration is explicit."}
