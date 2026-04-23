"""Add worker run records

Revision ID: 20260411_0022
Revises: 20260411_0021
Create Date: 2026-04-11 18:45:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260411_0022"
down_revision: Union[str, Sequence[str], None] = "20260411_0021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "worker_runs",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("worker_user_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("run_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("run_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_before", sa.DateTime(timezone=True), nullable=False),
        sa.Column("requested_limit", sa.Integer(), nullable=False),
        sa.Column("claimed_automation_task_count", sa.Integer(), nullable=False),
        sa.Column("completed_automation_task_count", sa.Integer(), nullable=False),
        sa.Column("failed_automation_task_count", sa.Integer(), nullable=False),
        sa.Column("processed_score_request_count", sa.Integer(), nullable=False),
        sa.Column("failed_score_request_count", sa.Integer(), nullable=False),
        sa.Column("cleaned_consent_reminder_count", sa.Integer(), nullable=False),
        sa.Column("cleaned_stale_follow_up_count", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.String(length=1000), nullable=True),
        sa.ForeignKeyConstraint(["worker_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_worker_runs_worker_user_id", "worker_runs", ["worker_user_id"], unique=False)
    op.create_index("ix_worker_runs_status", "worker_runs", ["status"], unique=False)
    op.create_index("ix_worker_runs_run_started_at", "worker_runs", ["run_started_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_worker_runs_run_started_at", table_name="worker_runs")
    op.drop_index("ix_worker_runs_status", table_name="worker_runs")
    op.drop_index("ix_worker_runs_worker_user_id", table_name="worker_runs")
    op.drop_table("worker_runs")
