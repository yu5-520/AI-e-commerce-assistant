"""Add DataVersion and AlertEvent production tables.

Revision ID: 20260623_535
Revises: 20260623_530
Create Date: 2026-06-23
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260623_535"
down_revision = "20260623_530"
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


def upgrade() -> None:
    op.create_table(
        "data_versions",
        sa.Column("data_version", sa.String(length=96), primary_key=True),
        sa.Column("import_job_id", sa.String(length=64), sa.ForeignKey("import_jobs.import_job_id"), nullable=True),
        sa.Column("dataset_name", sa.String(length=128), nullable=True),
        sa.Column("source_type", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_by", sa.String(length=64), nullable=True),
        sa.Column("updated_by", sa.String(length=64), nullable=True),
        trace_column(),
        *tenant_columns(),
    )
    op.create_table(
        "alert_events",
        sa.Column("alert_id", sa.String(length=64), primary_key=True),
        sa.Column("data_version", sa.String(length=96), nullable=True),
        sa.Column("source_module", sa.String(length=64), nullable=True),
        sa.Column("source_entity_id", sa.String(length=96), nullable=True),
        sa.Column("alert_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        trace_column(),
        *tenant_columns(),
    )
    for table in ["data_versions", "alert_events"]:
        op.create_index(f"idx_{table}_tenant_org", table, ["tenant_id", "org_id"])
        op.create_index(f"idx_{table}_deleted_at", table, ["deleted_at"])
        op.create_index(f"idx_{table}_trace_id", table, ["trace_id"])
    op.create_index("idx_data_versions_import", "data_versions", ["import_job_id"])
    op.create_index("idx_data_versions_dataset", "data_versions", ["dataset_name"])
    op.create_index("idx_alert_events_data_version", "alert_events", ["data_version"])
    op.create_index("idx_alert_events_source", "alert_events", ["source_module", "source_entity_id"])
    op.create_index("idx_alert_events_status", "alert_events", ["severity", "status"])


def downgrade() -> None:
    op.drop_table("alert_events")
    op.drop_table("data_versions")
