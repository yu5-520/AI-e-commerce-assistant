"""Initial P0 production schema scaffold.

Revision ID: 20260623_530
Revises:
Create Date: 2026-06-23
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260623_530"
down_revision = None
branch_labels = None
depends_on = None


def tenant_columns() -> list[sa.Column]:
    return [
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("org_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.String(length=64), nullable=True),
        sa.Column("delete_reason", sa.String(length=255), nullable=True),
    ]


def trace_column() -> sa.Column:
    return sa.Column("trace_id", sa.String(length=96), nullable=True)


def json_col(name: str) -> sa.Column:
    return sa.Column(name, sa.JSON(), nullable=True)


def create_common_indexes(table: str) -> None:
    op.create_index(f"idx_{table}_tenant_org", table, ["tenant_id", "org_id"])
    op.create_index(f"idx_{table}_deleted_at", table, ["deleted_at"])


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("tenant_id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.String(length=64), nullable=True),
        sa.Column("delete_reason", sa.String(length=255), nullable=True),
    )

    op.create_table("organizations", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(255), nullable=False), sa.Column("status", sa.String(32), nullable=False, server_default="active"), *tenant_columns())
    op.create_table("users", sa.Column("user_id", sa.String(64), primary_key=True), sa.Column("display_name", sa.String(255), nullable=False), sa.Column("role_id", sa.String(64), nullable=False), sa.Column("status", sa.String(32), nullable=False, server_default="active"), *tenant_columns())
    op.create_table("stores", sa.Column("store_id", sa.String(64), primary_key=True), sa.Column("store_name", sa.String(255), nullable=False), sa.Column("platform", sa.String(64), nullable=True), sa.Column("operator_user_id", sa.String(64), nullable=True), sa.Column("status", sa.String(32), nullable=False, server_default="active"), *tenant_columns())

    op.create_table("import_jobs", sa.Column("import_job_id", sa.String(64), primary_key=True), sa.Column("dataset_name", sa.String(128)), sa.Column("source_type", sa.String(64)), sa.Column("status", sa.String(32), nullable=False), sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("alert_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("task_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("data_version", sa.String(96)), json_col("input_snapshot"), json_col("output_snapshot"), sa.Column("error_message", sa.Text()), sa.Column("created_by", sa.String(64)), sa.Column("updated_by", sa.String(64)), trace_column(), *tenant_columns())
    op.create_table("projection_jobs", sa.Column("projection_job_id", sa.String(64), primary_key=True), sa.Column("import_job_id", sa.String(64), sa.ForeignKey("import_jobs.import_job_id"), nullable=False), sa.Column("projection_type", sa.String(64), nullable=False), sa.Column("status", sa.String(32), nullable=False), json_col("input_snapshot"), json_col("output_snapshot"), sa.Column("error_message", sa.Text()), trace_column(), *tenant_columns())
    op.create_table("decision_tasks", sa.Column("task_id", sa.String(64), primary_key=True), sa.Column("source_module", sa.String(64)), sa.Column("source_entity_id", sa.String(96)), sa.Column("title", sa.String(255), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("priority", sa.String(32)), sa.Column("assigned_to", sa.String(64)), sa.Column("due_at", sa.String(64)), json_col("payload"), sa.Column("created_by", sa.String(64)), sa.Column("updated_by", sa.String(64)), trace_column(), *tenant_columns())
    op.create_table("task_events", sa.Column("event_id", sa.String(64), primary_key=True), sa.Column("task_id", sa.String(64), sa.ForeignKey("decision_tasks.task_id"), nullable=False), sa.Column("event_type", sa.String(64), nullable=False), sa.Column("actor_id", sa.String(64)), json_col("payload"), trace_column(), *tenant_columns())
    op.create_table("task_evidence", sa.Column("evidence_id", sa.String(64), primary_key=True), sa.Column("task_id", sa.String(64), sa.ForeignKey("decision_tasks.task_id"), nullable=False), sa.Column("submitter_id", sa.String(64)), sa.Column("evidence_type", sa.String(64), nullable=False), sa.Column("note", sa.Text()), json_col("payload"), trace_column(), *tenant_columns())
    op.create_table("worker_jobs", sa.Column("worker_job_id", sa.String(64), primary_key=True), sa.Column("queue_name", sa.String(64), nullable=False), sa.Column("job_type", sa.String(64), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("priority", sa.Integer(), nullable=False, server_default="50"), sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"), sa.Column("idempotency_key", sa.String(128)), sa.Column("correlation_id", sa.String(128)), json_col("payload"), json_col("result"), sa.Column("error_message", sa.Text()), sa.Column("created_by", sa.String(64)), sa.Column("updated_by", sa.String(64)), trace_column(), *tenant_columns(), sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_worker_jobs_tenant_idempotency"))
    op.create_table("audit_logs", sa.Column("audit_id", sa.String(64), primary_key=True), sa.Column("actor_id", sa.String(64)), sa.Column("event_type", sa.String(96), nullable=False), sa.Column("resource_type", sa.String(64)), sa.Column("resource_id", sa.String(96)), sa.Column("action", sa.String(96)), sa.Column("status", sa.String(32)), json_col("payload"), trace_column(), *tenant_columns())
    op.create_table("tech_logs", sa.Column("log_id", sa.String(64), primary_key=True), sa.Column("actor_id", sa.String(64)), sa.Column("level", sa.String(16), nullable=False), sa.Column("logger", sa.String(64)), sa.Column("event_type", sa.String(96), nullable=False), sa.Column("message", sa.Text()), json_col("payload"), trace_column(), *tenant_columns())
    op.create_table("llm_gateway_events", sa.Column("event_id", sa.String(64), primary_key=True), sa.Column("user_id", sa.String(64)), sa.Column("event_type", sa.String(64), nullable=False), sa.Column("provider", sa.String(64)), sa.Column("model", sa.String(128)), sa.Column("prompt_name", sa.String(128)), sa.Column("schema_name", sa.String(128)), sa.Column("status", sa.String(32), nullable=False), sa.Column("cache_key", sa.String(128)), sa.Column("request_hash", sa.String(128)), sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"), json_col("payload"), trace_column(), *tenant_columns())

    for table in ["organizations", "users", "stores", "import_jobs", "projection_jobs", "decision_tasks", "task_events", "task_evidence", "worker_jobs", "audit_logs", "tech_logs", "llm_gateway_events"]:
        create_common_indexes(table)
        op.create_index(f"idx_{table}_trace_id", table, ["trace_id"])


def downgrade() -> None:
    for table in ["llm_gateway_events", "tech_logs", "audit_logs", "worker_jobs", "task_evidence", "task_events", "decision_tasks", "projection_jobs", "import_jobs", "stores", "users", "organizations", "tenants"]:
        op.drop_table(table)
