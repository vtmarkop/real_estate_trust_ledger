"""Add automation tasks for reminders and follow-ups

Revision ID: 20260411_0016
Revises: 20260411_0015
Create Date: 2026-04-11 07:10:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260411_0016"
down_revision: Union[str, Sequence[str], None] = "20260411_0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "automation_tasks",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("details", sa.String(length=1000), nullable=True),
        sa.Column("result_notes", sa.String(length=1000), nullable=True),
        sa.Column("subject_user_id", sa.Uuid(), nullable=True),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("consent_id", sa.Uuid(), nullable=True),
        sa.Column("requested_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("processed_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("dedupe_key", sa.String(length=255), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["consent_id"], ["trust_report_consents.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["processed_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["subject_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dedupe_key"),
    )
    op.create_index(op.f("ix_automation_tasks_consent_id"), "automation_tasks", ["consent_id"], unique=False)
    op.create_index(op.f("ix_automation_tasks_organization_id"), "automation_tasks", ["organization_id"], unique=False)
    op.create_index(op.f("ix_automation_tasks_processed_by_user_id"), "automation_tasks", ["processed_by_user_id"], unique=False)
    op.create_index(op.f("ix_automation_tasks_requested_by_user_id"), "automation_tasks", ["requested_by_user_id"], unique=False)
    op.create_index(op.f("ix_automation_tasks_scheduled_for"), "automation_tasks", ["scheduled_for"], unique=False)
    op.create_index(op.f("ix_automation_tasks_status"), "automation_tasks", ["status"], unique=False)
    op.create_index(op.f("ix_automation_tasks_subject_user_id"), "automation_tasks", ["subject_user_id"], unique=False)
    op.create_index(op.f("ix_automation_tasks_task_type"), "automation_tasks", ["task_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_automation_tasks_task_type"), table_name="automation_tasks")
    op.drop_index(op.f("ix_automation_tasks_subject_user_id"), table_name="automation_tasks")
    op.drop_index(op.f("ix_automation_tasks_status"), table_name="automation_tasks")
    op.drop_index(op.f("ix_automation_tasks_scheduled_for"), table_name="automation_tasks")
    op.drop_index(op.f("ix_automation_tasks_requested_by_user_id"), table_name="automation_tasks")
    op.drop_index(op.f("ix_automation_tasks_processed_by_user_id"), table_name="automation_tasks")
    op.drop_index(op.f("ix_automation_tasks_organization_id"), table_name="automation_tasks")
    op.drop_index(op.f("ix_automation_tasks_consent_id"), table_name="automation_tasks")
    op.drop_table("automation_tasks")
