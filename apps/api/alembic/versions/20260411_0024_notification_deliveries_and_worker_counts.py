"""add notification deliveries and worker notification counters

Revision ID: 20260411_0024
Revises: 20260411_0023
Create Date: 2026-04-11 20:40:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260411_0024"
down_revision = "20260411_0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("worker_runs", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "claimed_notification_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.add_column(
            sa.Column(
                "sent_notification_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.add_column(
            sa.Column(
                "failed_notification_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )

    op.create_table(
        "notification_deliveries",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("template_key", sa.String(length=100), nullable=False),
        sa.Column("recipient_user_id", sa.Uuid(), nullable=True),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("consent_id", sa.Uuid(), nullable=True),
        sa.Column("automation_task_id", sa.Uuid(), nullable=True),
        sa.Column("requested_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("processed_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("recipient_address", sa.String(length=320), nullable=False),
        sa.Column("subject_line", sa.String(length=255), nullable=False),
        sa.Column("body_text", sa.String(length=4000), nullable=False),
        sa.Column("dedupe_key", sa.String(length=255), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["automation_task_id"], ["automation_tasks.id"]),
        sa.ForeignKeyConstraint(["consent_id"], ["trust_report_consents.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["processed_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["recipient_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dedupe_key"),
    )
    op.create_index(
        "ix_notification_deliveries_automation_task_id",
        "notification_deliveries",
        ["automation_task_id"],
        unique=False,
    )
    op.create_index(
        "ix_notification_deliveries_channel",
        "notification_deliveries",
        ["channel"],
        unique=False,
    )
    op.create_index(
        "ix_notification_deliveries_consent_id",
        "notification_deliveries",
        ["consent_id"],
        unique=False,
    )
    op.create_index(
        "ix_notification_deliveries_organization_id",
        "notification_deliveries",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_notification_deliveries_processed_by_user_id",
        "notification_deliveries",
        ["processed_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_notification_deliveries_recipient_user_id",
        "notification_deliveries",
        ["recipient_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_notification_deliveries_requested_by_user_id",
        "notification_deliveries",
        ["requested_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_notification_deliveries_scheduled_for",
        "notification_deliveries",
        ["scheduled_for"],
        unique=False,
    )
    op.create_index(
        "ix_notification_deliveries_status",
        "notification_deliveries",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_notification_deliveries_template_key",
        "notification_deliveries",
        ["template_key"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_notification_deliveries_template_key", table_name="notification_deliveries")
    op.drop_index("ix_notification_deliveries_status", table_name="notification_deliveries")
    op.drop_index("ix_notification_deliveries_scheduled_for", table_name="notification_deliveries")
    op.drop_index("ix_notification_deliveries_requested_by_user_id", table_name="notification_deliveries")
    op.drop_index("ix_notification_deliveries_recipient_user_id", table_name="notification_deliveries")
    op.drop_index("ix_notification_deliveries_processed_by_user_id", table_name="notification_deliveries")
    op.drop_index("ix_notification_deliveries_organization_id", table_name="notification_deliveries")
    op.drop_index("ix_notification_deliveries_consent_id", table_name="notification_deliveries")
    op.drop_index("ix_notification_deliveries_channel", table_name="notification_deliveries")
    op.drop_index("ix_notification_deliveries_automation_task_id", table_name="notification_deliveries")
    op.drop_table("notification_deliveries")

    with op.batch_alter_table("worker_runs", schema=None) as batch_op:
        batch_op.drop_column("failed_notification_count")
        batch_op.drop_column("sent_notification_count")
        batch_op.drop_column("claimed_notification_count")
